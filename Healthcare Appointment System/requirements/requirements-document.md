# Healthcare Appointment System — Requirements Document

**Document Version:** 2.0.0
**Status:** Approved
**Last Updated:** 2025-07-14
**Owner:** Product Management — Digital Health Platform

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision and Scope](#2-product-vision-and-scope)
3. [Stakeholder Analysis](#3-stakeholder-analysis)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Compliance Requirements](#6-compliance-requirements)
7. [Integration Requirements](#7-integration-requirements)
8. [Constraints and Assumptions](#8-constraints-and-assumptions)
9. [Glossary](#9-glossary)

---

## 1. Executive Summary

The Healthcare Appointment System (HAS) is a multi-tenant, HIPAA-compliant platform designed to digitize and streamline the full lifecycle of outpatient care scheduling — from patient self-service booking through provider schedule management, insurance eligibility verification, referral routing, telehealth delivery, and post-visit communications. Healthcare organizations today operate fragmented scheduling workflows across phone-based intake, proprietary EHR portals, and manual insurance verification, resulting in high administrative overhead, patient no-show rates averaging 18–25%, and delayed access to care. HAS directly addresses these inefficiencies by providing a unified, API-first platform that integrates with existing EHR systems, insurance clearinghouses, and communication providers while enforcing rigorous data governance controls.

The strategic goals of HAS are threefold. First, reduce administrative burden on clinic staff by automating insurance eligibility checks, appointment reminders, and referral routing — targeting a 40% reduction in front-desk phone volume within 12 months of deployment. Second, improve patient access and satisfaction by offering 24/7 self-service scheduling, real-time slot availability, and proactive communications, with a target Net Promoter Score (NPS) above 65. Third, provide clinic administrators and compliance officers with the operational visibility and audit infrastructure needed to meet HIPAA, SOC 2 Type II, and applicable state telehealth regulations, eliminating manual compliance reporting.

Key expected outcomes include: appointment booking completion rate above 85% for self-service digital flows; insurance eligibility verification response times under 3 seconds for 95% of real-time queries; provider schedule utilization improvement of at least 15 percentage points through waitlist management and intelligent slot reuse; and zero patient PHI exposure incidents attributable to platform vulnerabilities. HAS will serve as the scheduling backbone for outpatient practices with 1 to 500 providers, supporting both single-location independent clinics and multi-site health system groups under a single multi-tenant deployment model.

---

## 2. Product Vision and Scope

### 2.1 Vision Statement

To be the most trusted scheduling infrastructure for outpatient healthcare — one that feels effortless for patients, empowering for clinicians, and provably compliant for administrators — by unifying every step of the appointment journey into a single, auditable, interoperable platform.

### 2.2 In-Scope Features

- Patient self-registration, profile management, and demographic data collection
- Provider profile management including specialties, credentials, and schedule templates
- Appointment scheduling: new, follow-up, recurring, same-day, and waitlist bookings
- Real-time and batch insurance eligibility verification via X12 270/271 transactions
- Referral creation, routing, and status tracking
- Appointment lifecycle management: confirmation, check-in, no-show, cancellation, rescheduling
- Telehealth video visit scheduling and session launch integration
- Multi-channel notifications: email, SMS, in-app (push), and voice via configurable providers
- Copay estimation and collection at time of booking
- Referral authorization tracking and prior authorization status management
- Patient intake forms and consent document collection pre-visit
- Operational dashboards and exportable reports for utilization, no-show, and revenue cycle metrics
- HIPAA-compliant audit logging for all PHI access and state transitions
- Multi-tenant administration: tenant onboarding, policy configuration, and user role management
- RESTful and webhook APIs for third-party integration

### 2.3 Out-of-Scope Items

- Clinical documentation, SOAP notes, and Electronic Health Record (EHR) chart authoring — HAS integrates with but does not replace EHR systems
- Prescription management and e-prescribing
- Medical billing claim adjudication and remittance advice processing — HAS provides eligibility and copay data but does not submit or reconcile claims
- Pharmacy integrations and medication dispensing workflows
- Inpatient and emergency department scheduling
- Lab order management and results delivery
- Human resources and staff payroll processing
- Custom EHR module development for individual tenants
- Direct consumer health wearable device integrations

---

## 3. Stakeholder Analysis

| Role | Goals | Pain Points | Success Metrics |
|---|---|---|---|
| **Patient** | Book appointments quickly without phone calls; receive timely reminders; understand out-of-pocket costs before visits; access telehealth conveniently | Long hold times to schedule; unexpected bills due to eligibility surprises; missed reminders; difficulty finding in-network providers | Self-service booking rate ≥ 85%; appointment reminder open rate ≥ 70%; patient NPS ≥ 65; copay surprise complaints = 0 |
| **Provider / Clinician** | Arrive at each visit with complete, prepared patients; minimize schedule gaps and no-shows; review upcoming caseload efficiently; launch telehealth sessions without friction | Patients arriving without completed intake; high no-show rate; gaps from last-minute cancellations; double-bookings; video session technical issues | No-show rate reduction ≥ 30%; intake completion rate ≥ 90% pre-visit; telehealth session launch failure rate < 1% |
| **Clinic Administrator** | Maximize provider utilization; reduce front-desk call volume; configure scheduling rules per provider and location; access real-time operational dashboards | Manual phone scheduling dominates staff time; insurance verification done call-by-call; no unified view across providers; difficulty configuring complex scheduling rules | Front-desk call volume reduction ≥ 40%; eligibility auto-verification rate ≥ 95%; schedule utilization improvement ≥ 15 pp |
| **Insurance Coordinator** | Verify patient eligibility before visits; track prior authorization status; reduce claim denials from eligibility issues | Real-time eligibility checks are slow or manual; prior auth status not visible in scheduling tools; no automated alerts when coverage lapses | Eligibility verification time < 3 s for 95% of queries; prior auth tracking accuracy = 100%; eligibility-related denial rate reduction ≥ 50% |
| **IT / System Administrator** | Maintain platform uptime; manage tenant onboarding and configuration; monitor integrations; enforce security policies | EHR integration complexity; keeping API credentials and certificates current; no centralized monitoring across tenants; compliance audit preparation is manual | Platform availability ≥ 99.9%; integration error rate < 0.1%; audit log export available within 1 hour of request |
| **Compliance Officer** | Ensure all PHI handling meets HIPAA minimum necessary standard; maintain audit trails; manage Business Associate Agreements; prepare for SOC 2 Type II audits | Disparate audit logs across systems; no automated PHI access reports; BAA management is manual; breach detection is reactive | 100% of PHI access events captured in audit log; BAA tracking coverage = 100% of vendor relationships; automated breach detection alerting within 15 minutes of anomaly |

---

## 4. Functional Requirements

### 4.1 Patient Management

---

**FR-01 — Patient Self-Registration**
**Priority:** Must
**Description:** The system shall allow patients to self-register by providing their demographic information, creating a secure account with email/phone verification, and accepting the platform's terms of service and HIPAA Notice of Privacy Practices.
**Acceptance Criteria:**
- Registration form collects first name, last name, date of birth, sex assigned at birth, gender identity (optional), email address, mobile phone, and mailing address.
- Email or SMS one-time passcode (OTP) verification is required before account activation; OTP expires in 10 minutes.
- A digitally timestamped acknowledgment of the HIPAA Notice of Privacy Practices is stored in the patient's audit record.
- Duplicate detection prevents creation of a second account for the same email address; the system returns HTTP 409 with a recovery prompt.
- Registration completes end-to-end in under 3 minutes under normal conditions (measured from form submission to confirmed account activation).

---

**FR-02 — Patient Profile Management**
**Priority:** Must
**Description:** The system shall allow authenticated patients to view and update their demographic profile, preferred communication channels, communication preferences (language, quiet hours), and emergency contact information.
**Acceptance Criteria:**
- Patients can update any demographic field except date of birth without contacting support; date of birth changes require staff verification.
- All profile changes are written to the immutable audit log with timestamp, actor, and before/after field values.
- Preferred language selection stores an IETF BCP-47 language tag and is propagated to all outbound notification templates.
- Communication opt-out per channel (SMS, email, push) takes effect within 60 seconds and is honored on all subsequent notification dispatches.

---

**FR-03 — Patient Search and Lookup**
**Priority:** Must
**Description:** Clinic staff shall be able to search for existing patients using combinations of name, date of birth, phone number, email address, and medical record number (MRN).
**Acceptance Criteria:**
- Search returns results within 500 ms for datasets up to 5 million patient records.
- Partial name matching (minimum 3 characters) is supported.
- Search results are limited to 50 records per query with pagination; each result displays name, DOB, MRN, and last visit date.
- All staff patient searches are recorded in the PHI access audit log, including search parameters and the ID of the requesting staff member.
- Patients are not returned in search results if their record has been suppressed due to a sensitive care flag (e.g., behavioral health, substance use) unless the requesting role has explicit sensitive-record access permission.

---

**FR-04 — Patient Insurance Information Management**
**Priority:** Must
**Description:** The system shall allow patients and authorized staff to add, update, and remove insurance plans associated with a patient's profile, including primary, secondary, and tertiary payer configurations.
**Acceptance Criteria:**
- Each insurance record stores: payer name, payer ID (PAYERID), member ID, group number, plan name, relationship to subscriber, and effective/termination dates.
- Patients can upload front and back images of their insurance card; images are stored in encrypted object storage and linked to the insurance record.
- The system validates that the payer ID resolves to a known clearinghouse payer before saving.
- Insurance records retain a full version history; deleted records are soft-deleted and recoverable by administrators within 90 days.

---

**FR-05 — Patient Portal Access Controls**
**Priority:** Must
**Description:** The system shall support authorized representative access, allowing a patient to designate a parent, guardian, or personal representative who may manage scheduling on their behalf.
**Acceptance Criteria:**
- Representatives are linked to a patient record with a relationship type (e.g., parent, legal guardian, spouse) and explicit authorization scope (view-only or full scheduling rights).
- Representative authorization requires a signed digital consent form stored in the patient's audit record.
- Representative access can be revoked by the patient at any time; revocation takes effect immediately.
- All actions taken by a representative are attributed to the representative's user ID in audit logs, with the patient's ID recorded as the subject.

---

### 4.2 Provider Management

---

**FR-06 — Provider Profile Management**
**Priority:** Must
**Description:** Administrators shall be able to create and maintain provider profiles, including clinical credentials, specialties, practice locations, accepted insurance plans, visit types offered, and NPI number.
**Acceptance Criteria:**
- Provider profiles capture: full legal name, NPI (10-digit, validated via NPI Registry format check), DEA number (optional), specialties (SNOMED-CT coded), board certifications, affiliated locations, and accepted payer list.
- Profiles include a publicly visible bio, photo, and languages spoken used to populate the patient-facing provider directory.
- A provider cannot be set to `ACTIVE` status without a valid NPI and at least one affiliated location.
- Changes to accepted insurance plans trigger a re-evaluation of all future appointments and flag any newly out-of-network cases for staff review.

---

**FR-07 — Provider Schedule Template Management**
**Priority:** Must
**Description:** Providers and their administrative delegates shall be able to define recurring weekly schedule templates per location, specifying available hours, visit type capacity, and buffer times between appointments.
**Acceptance Criteria:**
- Schedule templates are configured per provider per location with day-of-week, start time, end time, visit durations by visit type, and maximum concurrent appointments.
- Templates support buffer periods (0–60 minutes) between appointments to account for documentation and room turnover.
- Activating a new template applies to future dates only; existing confirmed appointments are not altered.
- Overlapping template rules for the same provider-location-time combination are rejected with a validation error identifying the conflicting rule.

---

**FR-08 — Provider Availability Overrides**
**Priority:** Must
**Description:** Providers and administrators shall be able to create ad-hoc availability overrides including time-off blocks, clinic closures, and temporary capacity expansions.
**Acceptance Criteria:**
- Overrides can be created for single dates or date ranges and apply to all visit types or specific visit types.
- Creating a closure override that conflicts with existing confirmed appointments automatically generates a worklist task for staff to rebook affected patients within 24 hours.
- Override creation, modification, and deletion are recorded in the provider audit trail with actor and timestamp.
- Emergency closure overrides applied within 2 hours of the affected slots trigger immediate patient SMS and email notifications.

---

**FR-09 — Provider Directory and Search**
**Priority:** Must
**Description:** Patients shall be able to search for providers by specialty, location (geographic proximity or specific clinic), insurance acceptance, visit type, gender, and language spoken.
**Acceptance Criteria:**
- Geographic search accepts a ZIP code and radius (default 25 miles) and returns results sorted by distance.
- Specialty search is driven by SNOMED-CT codes with a curated patient-friendly label mapping (e.g., "Cardiology" maps to code 394579002).
- Results filter by accepted insurance based on the patient's active insurance plan on file; unfiltered search is available for patients without insurance on file.
- Providers marked as `NOT_ACCEPTING_NEW_PATIENTS` are excluded from new patient search results but remain visible if a patient has a prior visit relationship.
- Search results return within 400 ms for up to 10,000 active providers.

---

**FR-10 — Provider Credential Verification and Expiry Tracking**
**Priority:** Should
**Description:** The system shall track expiration dates for key provider credentials (licenses, board certifications, DEA registration) and alert administrators prior to expiration.
**Acceptance Criteria:**
- Administrators can record credential type, issuing authority, issue date, expiration date, and a scanned copy of the credential document for each provider.
- The system generates an automated alert to the clinic administrator 90 days and 30 days before a credential expires.
- Providers with an expired primary state license are automatically set to `SCHEDULE_SUSPENDED` status and cannot accept new appointments until the credential is renewed.
- Credential expiry history is retained indefinitely and included in compliance audit exports.

---

### 4.3 Appointment Scheduling

---

**FR-11 — Real-Time Slot Availability Query**
**Priority:** Must
**Description:** The system shall expose available appointment slots in real time based on provider schedule templates, overrides, existing bookings, and visit type durations.
**Acceptance Criteria:**
- Slot availability queries return results within 200 ms at the 99th percentile under a load of 500 concurrent users.
- Slots are returned in chronological order and grouped by date; each slot includes provider ID, location ID, visit type, start time, end time, and a short-lived reservation token valid for 10 minutes.
- Slots held by an active reservation token are not returned as available to other queries until the token expires or is released.
- Queries support filtering by date range (up to 90 days), visit type, and provider.

---

**FR-12 — Patient Self-Service Appointment Booking**
**Priority:** Must
**Description:** Authenticated patients shall be able to book appointments by selecting a provider, available slot, visit type, and reason for visit, completing any required pre-booking intake questions, and confirming the appointment.
**Acceptance Criteria:**
- The booking flow can be completed in under 4 minutes for a returning patient with insurance on file (measured from slot selection to booking confirmation).
- Booking requires a valid reservation token; submitting an expired token returns HTTP 409 with the three next available slots as alternatives.
- A booking confirmation number is generated and displayed immediately upon successful booking; a confirmation message is dispatched to the patient's preferred channel within 60 seconds.
- Concurrent booking attempts for the same slot with the same reservation token are serialized; only the first succeeds, and subsequent attempts return HTTP 409.

---

**FR-13 — Staff-Assisted Appointment Booking**
**Priority:** Must
**Description:** Authorized clinic staff shall be able to book appointments on behalf of patients, including same-day and override bookings that bypass standard availability rules with documented justification.
**Acceptance Criteria:**
- Staff booking requires selection of an existing patient record (by search) or creation of a new patient record inline.
- Override bookings that exceed provider capacity require the booking staff member to enter a free-text clinical justification, which is stored in the appointment audit record.
- Staff can book on behalf of patients who do not have a patient portal account; the system creates a record in `STAFF_MANAGED` mode.
- All staff-created appointments are flagged with the staff member's user ID as the booking agent in audit logs.

---

**FR-14 — Appointment Rescheduling**
**Priority:** Must
**Description:** Patients and authorized staff shall be able to reschedule a confirmed appointment to a new date, time, or provider within configurable advance-notice windows.
**Acceptance Criteria:**
- Patient self-service rescheduling is available up to the number of hours before the appointment defined in the tenant's cancellation policy (minimum 2 hours, configurable up to 72 hours).
- Rescheduling generates a new booking confirmation and sends a reschedule notification to the patient within 60 seconds of confirmation.
- The original appointment record is retained with status `RESCHEDULED` and a forward reference to the replacement appointment ID.
- If the new slot's insurance acceptance differs from the original, the system presents a warning and requires explicit patient acknowledgment before confirming.

---

**FR-15 — Appointment Cancellation**
**Priority:** Must
**Description:** Patients and authorized staff shall be able to cancel appointments with a reason code; the system shall enforce tenant-configured late-cancellation policies including fee assessment.
**Acceptance Criteria:**
- Patients may cancel without fee up to the tenant-configured advance-notice threshold; cancellations inside the threshold trigger a no-show fee assessment if configured.
- Cancellation reason codes are drawn from a configurable tenant vocabulary; a free-text note is optional.
- Cancelled slots are immediately released and become visible to other patients and the waitlist engine within 30 seconds.
- Staff cancellations on behalf of the clinic (e.g., provider unavailability) do not trigger late-cancellation fees and automatically generate patient rebook outreach.

---

**FR-16 — Waitlist Management**
**Priority:** Should
**Description:** The system shall maintain per-provider, per-visit-type waitlists and automatically notify the next eligible patient when a cancellation creates an opening that matches their waitlist criteria.
**Acceptance Criteria:**
- Patients can join a waitlist for a specific provider, a specific specialty, or any provider at a specific location, with a preferred date range.
- When a slot opens, the system evaluates the waitlist in priority order (first registered, first served within the same urgency tier) and sends the first eligible patient an offer notification containing a time-limited booking link valid for 30 minutes.
- If the notified patient does not accept within 30 minutes, the offer is automatically passed to the next eligible patient.
- Waitlist enrollment, offer dispatch, acceptance, and expiry events are all recorded in the audit log.

---

**FR-17 — Recurring Appointment Series**
**Priority:** Should
**Description:** Providers and authorized staff shall be able to schedule recurring appointment series (e.g., weekly physical therapy, biweekly follow-up) for a defined number of occurrences or a date range.
**Acceptance Criteria:**
- Series can be configured with frequency (daily, weekly, bi-weekly, monthly), occurrence count (1–52), or end date.
- Each occurrence is created as an independent appointment record linked to a series ID, enabling individual cancellation or rescheduling without affecting the series.
- The system validates provider availability for all occurrences at the time of series creation and flags any dates where availability cannot be confirmed.
- Cancelling the entire series generates individual cancellation events and notifications for each future occurrence.

---

**FR-18 — No-Show Processing**
**Priority:** Must
**Description:** The system shall automatically mark appointments as `NO_SHOW` when a patient fails to check in within a configurable grace period after the scheduled start time, and shall initiate configurable follow-up workflows.
**Acceptance Criteria:**
- The grace period is configurable per tenant between 10 and 30 minutes after the scheduled appointment start time.
- No-show status transition triggers an automated outreach message to the patient offering rebooking, dispatched within 5 minutes of the status transition.
- No-show fee assessment follows the tenant's billing policy; assessed fees are recorded in the patient's billing record.
- No-show rate by provider and by patient is available in the operational analytics dashboard.

---

### 4.4 Insurance and Eligibility

---

**FR-19 — Real-Time Insurance Eligibility Verification**
**Priority:** Must
**Description:** The system shall automatically submit real-time X12 270 eligibility inquiries to insurance clearinghouses and parse X12 271 eligibility responses to determine patient coverage, copay, deductible status, and network status.
**Acceptance Criteria:**
- Real-time eligibility verification is triggered automatically when a patient with insurance on file books an appointment; response is parsed and stored within 5 seconds for 95% of requests.
- Eligibility responses populate the appointment record with: coverage active (yes/no), in-network status, copay amount by service type, deductible met amount, and remaining deductible.
- If the clearinghouse returns an error or timeout, the system retries once and flags the appointment for manual staff review; staff are alerted within 2 minutes.
- Eligibility results are cached per patient-payer pair for 24 hours; subsequent bookings within the cache window use stored results with a visible "last verified" timestamp.

---

**FR-20 — Batch Eligibility Verification**
**Priority:** Must
**Description:** The system shall run automated batch eligibility checks for all appointments scheduled within the next 5 business days and update appointment records with refreshed eligibility data.
**Acceptance Criteria:**
- Batch job runs nightly at a configurable time (default 11:00 PM tenant local time).
- Batch results update the eligibility record on each appointment; appointments where coverage has lapsed since booking are flagged with status `ELIGIBILITY_ALERT`.
- Appointments flagged `ELIGIBILITY_ALERT` generate a worklist task for the insurance coordinator and an outreach notification to the patient within 2 hours of batch completion.
- Batch job completion, total records processed, success count, and failure count are recorded in the system operations log.

---

**FR-21 — Copay Collection at Booking**
**Priority:** Should
**Description:** The system shall present the estimated copay to the patient during the booking flow and optionally collect copay payment at time of booking using a PCI-DSS compliant payment integration.
**Acceptance Criteria:**
- Copay estimate is displayed to the patient before booking confirmation using data from the most recent eligibility verification; the display includes a disclaimer that the amount is an estimate.
- Payment collection is optional and configurable per tenant and per visit type; tenants can require, encourage, or disable copay collection at booking.
- Successful payment generates a payment receipt number stored on the appointment record; failed payments do not block appointment confirmation if collection is configured as optional.
- Copay amounts collected at booking are reconcilable against EHR billing records via the appointment ID.

---

**FR-22 — Prior Authorization Tracking**
**Priority:** Should
**Description:** The system shall allow insurance coordinators to record prior authorization (PA) status for appointments, track PA expiration, and block appointment confirmation for visit types requiring PA until authorization is obtained.
**Acceptance Criteria:**
- Visit types can be flagged as PA-required in the tenant configuration; appointments of those types cannot reach `CONFIRMED` status without a recorded PA number and authorization date.
- PA records store: authorization number, authorized CPT codes, authorized units, authorization date, expiration date, and authorizing reviewer name.
- The system generates alerts 14 days and 3 days before a PA expiration date to the insurance coordinator.
- Appointments blocked pending PA are visible in a dedicated PA worklist dashboard filtered by urgency and scheduled date.

---

**FR-23 — Explanation of Benefits Display**
**Priority:** Could
**Description:** The system shall display a simplified Explanation of Benefits (EOB) summary to patients after their visit, sourced from payer EOB data provided via integration.
**Acceptance Criteria:**
- EOB data is ingested via the EHR/payer integration and linked to the corresponding appointment by claim number.
- Displayed EOB includes: billed amount, allowed amount, plan paid amount, patient responsibility, and payment status.
- EOB is available in the patient portal within 48 hours of the payer processing date.
- Patients can download EOB as a PDF; downloaded files are encrypted in transit and the download event is recorded in the audit log.

---

### 4.5 Referrals

---

**FR-24 — Outgoing Referral Creation**
**Priority:** Must
**Description:** Providers and authorized staff shall be able to create outgoing referrals to internal or external specialists, capturing the clinical reason, urgency, preferred timeline, and relevant diagnostic codes.
**Acceptance Criteria:**
- Referral records capture: referring provider NPI, receiving provider NPI (or external organization name), patient ID, referral date, clinical indication (free text plus ICD-10 code), urgency (routine/urgent/emergent), and preferred appointment window.
- Referrals to internal providers (within the same tenant) automatically create a pending appointment slot hold in the receiving provider's schedule for 72 hours.
- Referrals to external providers generate a structured referral document (PDF) that staff can transmit via fax or secure message integration.
- Each referral is assigned a unique referral ID used for status tracking throughout the workflow.

---

**FR-25 — Referral Status Tracking**
**Priority:** Must
**Description:** The system shall track the status of outgoing and incoming referrals through each stage of the referral workflow and provide visibility to the referring provider, receiving provider, and authorized staff.
**Acceptance Criteria:**
- Referral status values: `SENT`, `RECEIVED`, `APPOINTMENT_SCHEDULED`, `COMPLETED`, `DECLINED`, `EXPIRED`.
- Status transitions are timestamped and attributed to the actor (provider, staff, or system) in the referral audit trail.
- Referrals with no status update within the urgency-appropriate SLA (routine: 7 days; urgent: 48 hours; emergent: 4 hours) trigger an automated escalation alert to the referring provider's care team.
- Referring providers can view all outgoing referral statuses in a consolidated referral dashboard filterable by date range, status, and receiving provider.

---

**FR-26 — Incoming Referral Management**
**Priority:** Should
**Description:** The system shall enable receiving providers and their administrative staff to accept, decline, or route incoming referrals and directly schedule the referred patient from the referral record.
**Acceptance Criteria:**
- Incoming referrals are presented in a dedicated worklist sorted by urgency and referral date.
- Accepting a referral and scheduling the appointment from the referral record automatically links the appointment to the referral ID and updates the referral status to `APPOINTMENT_SCHEDULED`.
- Declining a referral requires a reason code and optional free-text note; the decline is communicated back to the referring provider via the messaging integration.
- Incoming referrals from external organizations can be entered manually by staff and are distinguished from system-generated referrals by a `MANUAL_ENTRY` source flag.

---

### 4.6 Notifications and Communications

---

**FR-27 — Appointment Confirmation Notifications**
**Priority:** Must
**Description:** The system shall send multi-channel appointment confirmation messages to patients immediately upon booking, rescheduling, or cancellation, containing all necessary appointment details and actionable links.
**Acceptance Criteria:**
- Confirmation messages are dispatched within 60 seconds of appointment status change for email and SMS; push notifications within 30 seconds.
- Confirmation messages include: provider name, clinic name, address, appointment date and time (in patient's local timezone), visit type, confirmation number, and a link to the patient portal.
- Telehealth appointments additionally include the video session join link, pre-visit technical requirements, and a test connection link.
- Message delivery status (sent, delivered, failed) is tracked per channel and stored on the appointment notification record.

---

**FR-28 — Appointment Reminder Notifications**
**Priority:** Must
**Description:** The system shall send configurable appointment reminders on a tenant-defined schedule (e.g., 72 hours and 24 hours before the appointment), including pre-visit intake instructions and intake form links.
**Acceptance Criteria:**
- Reminder schedule is configurable per tenant with up to 3 reminders per appointment; default schedule is 72 hours and 24 hours before appointment time.
- Reminders dispatched before incomplete intake forms are detected include a direct link to the intake form; reminders dispatched after intake is complete omit the intake link.
- Patients who have opted out of a specific channel (e.g., SMS) do not receive reminders via that channel; at least one reminder is always sent via a non-opted-out channel if any remain.
- Reminder delivery rate and open/click rate (for email) are tracked and available in the communications analytics dashboard.

---

**FR-29 — Secure In-App Messaging**
**Priority:** Should
**Description:** The system shall provide a HIPAA-compliant secure messaging channel between patients and their care team for non-urgent clinical questions, post-visit follow-up, and administrative communications.
**Acceptance Criteria:**
- Messages are encrypted at rest and in transit; PHI transmitted via secure messaging is never included in email or SMS notification bodies — only a "you have a new message" alert is sent.
- Care team members can respond on behalf of a provider's inbox; all responses are attributed to the responding staff member's identity in message metadata.
- Message threads are associated with the relevant appointment ID when initiated from an appointment context.
- Message delivery and read receipts are tracked; unread messages older than 48 hours generate an alert to the care team inbox manager.

---

**FR-30 — Communication Preference Management**
**Priority:** Must
**Description:** The system shall honor patient communication preferences including channel selection, language, time-zone-aware quiet hours, and regulatory opt-out requirements.
**Acceptance Criteria:**
- Quiet hours are configurable per patient (default 9 PM – 8 AM patient local time); messages queued during quiet hours are held and dispatched at the start of the next allowed window.
- HIPAA minimum-necessary rules are enforced: PHI in notification content is limited to the minimum data elements required to convey the message's purpose.
- CAN-SPAM and TCPA opt-out mechanisms are implemented for email and SMS respectively; opt-out processing completes within 10 business days per regulatory requirement but the system applies it immediately.
- Notification template content is available in a configurable set of languages (minimum: English and Spanish); language selection is driven by the patient's profile preferred language.

---

### 4.7 Reporting and Analytics

---

**FR-31 — Operational Scheduling Dashboard**
**Priority:** Must
**Description:** The system shall provide real-time operational dashboards for clinic administrators displaying key scheduling metrics including schedule utilization, no-show rate, cancellation rate, and average wait time to next available appointment.
**Acceptance Criteria:**
- Dashboard data refreshes every 5 minutes; users can manually trigger a refresh.
- Metrics are filterable by provider, location, specialty, visit type, and date range.
- Schedule utilization is calculated as (booked slots / available slots) × 100 and displayed as a percentage with trend sparklines for the prior 30 days.
- No-show rate, cancellation rate, and late-cancellation rate are displayed as percentages with drill-down to individual appointment records.

---

**FR-32 — Revenue Cycle Metrics Reporting**
**Priority:** Should
**Description:** The system shall provide exportable reports covering insurance eligibility verification outcomes, copay collection rates, prior authorization status, and referral conversion rates for use by clinic administrators and billing staff.
**Acceptance Criteria:**
- Reports are available in CSV and PDF formats; exports are initiated on demand or on a configurable automated schedule (daily, weekly, monthly).
- Revenue cycle reports exclude PHI in summary views; detail-level exports that include PHI require the requesting user to have the `REPORTS_PHI` permission, and the export event is recorded in the audit log.
- Eligibility verification outcomes report includes: total verifications, auto-verified, manual review required, coverage lapsed alerts, and eligibility-related denial count.
- Reports cover date ranges up to 24 months.

---

**FR-33 — Compliance Audit Log Export**
**Priority:** Must
**Description:** The system shall provide compliance officers and IT administrators with the ability to query and export the PHI access audit log for a specified date range, user, or patient record.
**Acceptance Criteria:**
- Audit log entries include: event timestamp (UTC), event type, actor user ID, actor role, patient record ID, data fields accessed or modified, source IP address, and request correlation ID.
- Audit log export is available as a signed, tamper-evident CSV file; the file hash is recorded in the audit system at export time.
- Audit log query and export capability is role-restricted to `COMPLIANCE_OFFICER` and `SYSTEM_ADMIN` roles.
- Audit log data is retained for a minimum of 6 years in compliance with HIPAA requirements and is immutable after write.

---

### 4.8 Administration

---

**FR-34 — Multi-Tenant Configuration Management**
**Priority:** Must
**Description:** System administrators shall be able to onboard new tenant organizations, configure tenant-level scheduling policies, and manage tenant user accounts and role assignments.
**Acceptance Criteria:**
- Tenant onboarding creates an isolated data partition, default role set, and configures required fields for HIPAA Notice of Privacy Practices and BAA reference.
- Tenant configuration covers: cancellation policy (advance notice window, fee amount), scheduling horizon (how far in advance patients can book), visit types, reminder schedule, copay policy, and accepted payer list.
- Role assignments follow a least-privilege model; roles are assigned per tenant and cannot be elevated to super-admin without a two-party approval workflow.
- Tenant configuration changes are versioned and auditable; rolling back to a previous configuration version is supported within 30 days.

---

**FR-35 — System Health Monitoring and Alerting**
**Priority:** Must
**Description:** The system shall expose health check endpoints and integrate with configurable alerting destinations to notify IT administrators of service degradation, integration failures, and approaching SLA breaches.
**Acceptance Criteria:**
- A `/health/live` endpoint returns HTTP 200 if the service process is alive; a `/health/ready` endpoint returns HTTP 200 only when all downstream dependencies (database, cache, message broker) are available.
- Alerting rules are configurable for: API error rate > 1% over 5 minutes, p99 response time > 500 ms over 5 minutes, integration circuit-breaker open events, and scheduled job failures.
- Alerts are routed to configurable destinations (email, PagerDuty webhook, Slack webhook) with severity tagging (critical/warning/info).
- Integration failure alerts include the integration name, error code, affected transaction count, and a link to the relevant runbook.

---

**FR-36 — Data Retention and Purge Management**
**Priority:** Must
**Description:** The system shall enforce configurable data retention policies per data category, automatically archive records reaching the retention threshold, and support compliant purge workflows for data subject deletion requests.
**Acceptance Criteria:**
- Retention policy is configurable per tenant per data category (patient records, appointment records, audit logs, notification logs) with minimum floors enforced by compliance rules (audit logs: 6 years; medical records: per state law, minimum 7 years for adults).
- Automated archival moves records past the active retention period to a cold-storage tier while keeping them queryable for compliance purposes.
- Patient deletion requests (HIPAA right of access revocation where applicable) are triaged through a review workflow; irreversible purge requires dual-approval from Compliance Officer and System Admin.
- Purge operations are recorded in the system audit log with the approving actors, date, data category, and record count.

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Target | Measurement Method |
|---|---|---|---|
| NFR-01 | API end-to-end response latency (patient-facing booking APIs) | p99 < 500 ms; p95 < 250 ms under 500 concurrent users | Synthetic load test with production-equivalent data volumes |
| NFR-02 | Slot availability query response time | p99 < 200 ms; p95 < 100 ms | Isolated endpoint load test at 1,000 req/s |
| NFR-03 | Real-time eligibility verification response (clearinghouse round-trip) | p95 < 3,000 ms; p99 < 8,000 ms | End-to-end trace including clearinghouse latency |
| NFR-04 | Notification dispatch latency (booking confirmation) | Email and SMS dispatched within 60 s; push within 30 s | Event timestamp to third-party provider acceptance timestamp |

### 5.2 Availability

| ID | Requirement | Target |
|---|---|---|
| NFR-05 | Patient-facing booking API monthly uptime | ≥ 99.9% (≤ 43.8 minutes unplanned downtime per month) |
| NFR-06 | Recovery Time Objective (RTO) / Recovery Point Objective (RPO) | RTO ≤ 30 minutes; RPO ≤ 5 minutes for appointment and patient data |

### 5.3 Scalability

| ID | Requirement | Target |
|---|---|---|
| NFR-07 | Peak concurrent user support | 10,000 concurrent authenticated sessions without performance degradation |
| NFR-08 | Daily booking throughput | 500,000 appointment bookings per day sustained; 50,000 bookings per hour at peak |

### 5.4 Security

| ID | Requirement | Detail |
|---|---|---|
| NFR-09 | Encryption at rest | All PHI and PII stored using AES-256 encryption; database encryption keys managed via a dedicated Key Management Service (KMS) with annual rotation |
| NFR-10 | Encryption in transit | All external and internal service communication requires TLS 1.2 minimum; TLS 1.3 preferred; TLS 1.0 and 1.1 are disabled |
| NFR-11 | Authentication requirements | All staff and provider accounts require multi-factor authentication (MFA); patient accounts require email or SMS verification at registration; session tokens expire after 30 minutes of inactivity |

### 5.5 Usability

| ID | Requirement | Detail |
|---|---|---|
| NFR-12 | Accessibility | All patient-facing web interfaces must conform to WCAG 2.1 Level AA; compliance verified by automated tooling and manual review with assistive technology |
| NFR-13 | Mobile responsiveness | All patient-facing interfaces must be fully functional on mobile devices with screen widths from 375 px (iPhone SE) to 428 px (iPhone 14 Pro Max) without horizontal scrolling |

### 5.6 Maintainability

| ID | Requirement | Target |
|---|---|---|
| NFR-14 | Automated test code coverage | Unit and integration test coverage ≥ 80% of production code paths; critical scheduling and eligibility paths require ≥ 95% coverage |
| NFR-15 | Deployment frequency and pipeline | Support continuous delivery with at least daily deployment capability to staging; production deployments achievable within 30 minutes via automated pipeline with rollback in under 10 minutes |

---

## 6. Compliance Requirements

### 6.1 HIPAA

**PHI Handling and Minimum Necessary Standard**
All access to Protected Health Information must be governed by the minimum necessary standard. Access controls must ensure that each role is granted access only to the PHI required to perform their defined job function. Role-based access is reviewed quarterly and validated against job descriptions. Bulk PHI exports require documented business justification and dual-approval authorization.

**Audit Logging**
Every access, creation, modification, and deletion of PHI must be logged in an immutable audit trail per 45 CFR § 164.312(b). Log entries must include: the identity of the person accessing the information, the date and time of access, the type of action performed, and the specific records accessed. Audit logs must be stored for a minimum of 6 years and protected against unauthorized modification or deletion.

**Breach Notification**
The system must detect potential breach indicators (anomalous data access volumes, unauthorized access attempts, bulk export by non-privileged accounts) and generate automated alerts within 15 minutes of detection. Breach investigation workflows must support documentation of the incident timeline, affected records, and notification status per 45 CFR § 164.400–414 (60-day notification requirement for breaches affecting 500 or more individuals).

**Business Associate Agreements (BAA)**
All third-party service providers that handle PHI on behalf of the platform (clearinghouses, email/SMS providers, cloud infrastructure providers, video conferencing providers) must execute a HIPAA-compliant BAA before integration activation. The compliance officer must maintain a current BAA registry with execution dates and renewal tracking. Integrations with vendors lacking an executed BAA must be blocked at the infrastructure level.

**Technical Safeguards**
Automatic session logoff after 30 minutes of inactivity is mandatory for all authenticated sessions. Encryption of PHI at rest and in transit per the standards defined in NFR-09 and NFR-10 is required. Transmission of PHI via unencrypted email or SMS body is prohibited; notification content must follow the minimum necessary standard with PHI restricted to the minimum required fields.

### 6.2 State Regulations

**Telehealth**
The system must enforce state-specific telehealth originating site requirements where applicable. Provider profiles must include their active state licenses; the scheduling engine must validate that a provider holds an active license in the patient's state of residence for telehealth visit types. State telehealth prescribing restrictions must be configurable per tenant to block specific visit types in non-compliant state combinations.

**Medical Records Retention**
Default medical records retention is set to 7 years for adult patients and until the patient's 21st birthday for minor patients, consistent with the minimum standard across most U.S. states. Tenants operating in states with longer mandatory retention periods (e.g., Massachusetts: 7 years; New York: 6 years for adults) must configure the longer period; the platform will enforce the longer of the tenant-configured period or the platform minimum.

**Prescription and Controlled Substance Restrictions**
The system does not support e-prescribing; however, visit type configurations may include flags indicating a visit is intended for controlled substance evaluation. These flags are surfaced to compliance staff and are included in audit exports for DEA compliance purposes.

### 6.3 SOC 2 Type II

The platform must maintain operational controls sufficient to support an annual SOC 2 Type II audit covering the Security, Availability, and Confidentiality trust service criteria. Key control requirements include:

- **Change Management:** All production code changes must be reviewed and approved before deployment; deployment history is retained for 12 months.
- **Access Management:** User access provisioning and de-provisioning must be completed within 1 business day of request; quarterly access reviews must document review completion and any access revocations.
- **Incident Management:** Security incidents must be classified, documented, and resolved according to a documented incident response procedure; post-incident reviews must be completed within 5 business days for severity-1 incidents.
- **Vulnerability Management:** Automated dependency vulnerability scanning must run on every code merge; critical vulnerabilities (CVSS ≥ 9.0) must be remediated within 7 days; high vulnerabilities (CVSS 7.0–8.9) within 30 days.
- **Backup and Recovery:** Database backups must run at least every 6 hours; restore procedures must be tested quarterly with documented RTO/RPO results.

---

## 7. Integration Requirements

### 7.1 EHR Systems — HL7 FHIR R4

The system must expose and consume HL7 FHIR R4 compliant APIs for bidirectional patient, appointment, and referral data exchange with EHR systems.

- **Patient ($match):** Patient demographic lookup must support the FHIR Patient `$match` operation to resolve patient identity across systems using probabilistic matching on name, DOB, and identifiers.
- **Appointment resource:** Booking events must create or update FHIR Appointment resources on the integrated EHR; status transitions in HAS must be reflected in EHR appointment status within 30 seconds via FHIR PATCH.
- **ServiceRequest resource:** Referrals created in HAS must be mirrored as FHIR ServiceRequest resources on the EHR.
- **SMART on FHIR:** The patient portal must support SMART on FHIR launch sequences to enable EHR-embedded scheduling workflows.
- **Error handling:** FHIR integration failures must trigger a circuit-breaker after 3 consecutive failures within 60 seconds; the system must queue failed operations for retry with exponential backoff up to 24 hours.

### 7.2 Insurance Clearinghouses — X12 270/271

Real-time and batch insurance eligibility verification must be implemented using X12 5010 270/271 transaction sets via certified clearinghouse connections.

- **270 Inquiry:** Eligibility inquiries must include: subscriber ID, group number, provider NPI, date of service, and service type code.
- **271 Response Parsing:** The system must parse benefit information segments (EB) for: coverage active status, in-network indicator, copay amount (VC/VS by service type), deductible (C) and remaining deductible (C remaining), and out-of-pocket maximum.
- **Clearinghouse SLA:** Integration must support the clearinghouse's published real-time response SLA; a configurable timeout (default: 8 seconds) triggers fallback to manual verification mode.
- **Supported clearinghouses:** Initial integration targets Availity and Change Healthcare; the integration layer must be built against an abstraction interface to support additional clearinghouse onboarding without core platform changes.

### 7.3 Payment Processors — PCI-DSS Compliance

Copay and fee collection must be integrated with a PCI-DSS Level 1 certified payment processor.

- **Tokenization:** The platform must never store raw card numbers (PAN); all payment method data must be tokenized at the point of capture using the processor's hosted fields or SDK.
- **Supported operations:** Authorization, capture, refund, and void must be supported; partial refunds must be supported for overpayment scenarios.
- **3D Secure:** 3DS2 authentication must be supported for card-not-present transactions.
- **Reconciliation:** Payment records in HAS must include processor transaction ID, settlement date, and settlement amount to support reconciliation against clinic bank statements.
- **Scope reduction:** The platform's network and application components must be scoped to PCI-DSS SAQ A-EP or equivalent; a current Attestation of Compliance (AOC) from the payment processor must be on file.

### 7.4 SMS and Email Providers

Multi-channel notification delivery must be implemented via integration with configurable third-party SMS and email providers.

- **SMS:** Primary integration with Twilio (or equivalent); messages must include an opt-out instruction ("Reply STOP to unsubscribe") per TCPA requirements; delivery receipts must be tracked via webhook.
- **Email:** Primary integration with SendGrid or AWS SES; DKIM and SPF authentication must be configured for sending domains; bounce and complaint webhooks must be processed to suppress invalid addresses automatically.
- **Provider failover:** If the primary provider returns an error or timeout (> 5 seconds), the system must route to a configured secondary provider for critical notification categories (booking confirmation, appointment reminder).
- **Template management:** Notification templates are managed in the platform admin UI with version history; template changes require approval before promotion to production.

### 7.5 Video Conferencing — Telehealth Sessions

Telehealth appointment types must integrate with a HIPAA-BAA-covered video conferencing provider.

- **Supported providers:** Zoom for Healthcare and Doxy.me are the target integrations; the integration must be built against an abstraction interface to support provider switching.
- **Session provisioning:** A unique video session must be created automatically when a telehealth appointment is confirmed; the patient join link and provider host link must be stored on the appointment record.
- **Session launch:** Patients and providers must be able to launch their video session directly from the appointment details page in the portal/dashboard without requiring an account with the video provider.
- **Session recording:** Session recording capabilities must be disabled by default; tenants with clinical documentation needs may enable recording with explicit patient consent captured and stored in the appointment record.
- **HIPAA BAA:** The video conferencing provider BAA must be executed and on file before enabling telehealth scheduling for any tenant.

---

## 8. Constraints and Assumptions

### Constraints

- **Regulatory floor:** The platform must operate within U.S. healthcare regulatory frameworks (HIPAA, HITECH, state telehealth laws) as a minimum baseline; international deployment is not in scope for the initial release.
- **EHR dependency:** The platform does not own the clinical record. Clinical decisions such as diagnosis, treatment planning, and prescribing remain in the EHR; HAS is limited to scheduling, communications, and administrative workflow data.
- **PCI scope minimization:** The platform must not store, process, or transmit raw cardholder data. All payment data handling must be delegated to the PCI-DSS certified payment processor to minimize compliance scope.
- **Clearinghouse contracts:** Real-time eligibility verification requires executed trading partner agreements and clearinghouse enrollment for each tenant; this onboarding process (typically 2–4 weeks per payer) is outside the platform's control and must be accounted for in tenant onboarding timelines.
- **Browser support:** The patient portal must support the current and prior major versions of Chrome, Firefox, Safari, and Edge. Internet Explorer is not supported.
- **Infrastructure:** The platform is deployed on cloud infrastructure (AWS or GCP); on-premises deployment is not supported in the initial release.

### Assumptions

- Each tenant organization will designate a technical point of contact responsible for EHR integration configuration and testing.
- Patients are assumed to have access to a smartphone or computer with internet connectivity; the platform does not provide offline scheduling capabilities beyond staff-assisted booking.
- Insurance payers are assumed to support X12 5010 270/271 transactions via the clearinghouse; payers that do not support electronic eligibility inquiry are handled via the manual verification fallback workflow.
- Providers are assumed to have completed NPI registration with the National Plan and Provider Enumeration System (NPPES) before being onboarded to the platform.
- Tenant administrators are responsible for ensuring their scheduling configuration (visit types, durations, capacity) accurately reflects their clinical operations; the platform enforces the rules as configured.
- BAA execution with all third-party service providers handling PHI is assumed to be a pre-activation requirement; activating a new tenant before BAA completion is a compliance violation and must be blocked by the onboarding workflow.

---

## 9. Glossary

| Term | Definition |
|---|---|
| **PHI (Protected Health Information)** | Any individually identifiable health information created, received, maintained, or transmitted by a covered entity or its business associates, as defined under HIPAA (45 CFR § 160.103). Includes demographic data that can identify a patient in relation to their health condition, treatment, or payment. |
| **HIPAA (Health Insurance Portability and Accountability Act)** | U.S. federal law enacted in 1996 establishing national standards for the protection of sensitive patient health information. HIPAA's Privacy Rule governs the use and disclosure of PHI; the Security Rule establishes technical, administrative, and physical safeguards for electronic PHI (ePHI). |
| **BAA (Business Associate Agreement)** | A contract required by HIPAA between a covered entity (e.g., a clinic) and a business associate (any vendor that handles PHI on the covered entity's behalf). The BAA defines the permitted uses of PHI and requires the business associate to implement appropriate safeguards. |
| **NPI (National Provider Identifier)** | A unique 10-digit identification number issued by the Centers for Medicare & Medicaid Services (CMS) to covered healthcare providers in the United States. NPIs are used in all HIPAA standard transactions and are required for claims submission and eligibility verification. |
| **CPT Code (Current Procedural Terminology)** | A standardized code set maintained by the American Medical Association (AMA) used to describe medical, surgical, and diagnostic services performed by providers. CPT codes are the primary basis for medical billing and are required on insurance claims. |
| **ICD-10 (International Classification of Diseases, 10th Revision)** | A diagnostic classification system maintained by the World Health Organization (WHO) and adapted for U.S. clinical use by the CDC. ICD-10-CM codes represent patient diagnoses and are required on insurance claims to justify medical necessity. |
| **Eligibility Verification** | The process of confirming a patient's insurance coverage status, benefits, copay obligations, deductible status, and network tier with their insurance payer before a healthcare visit. Performed electronically via X12 270/271 transactions or manually via payer portals. |
| **Referral** | A formal recommendation from one provider (the referring provider) to another provider or specialist (the receiving provider) for a patient to receive additional evaluation or treatment. Referrals may or may not require prior authorization from the patient's insurance plan. |
| **Prior Authorization (PA)** | A requirement by an insurance plan that a provider must obtain approval before delivering a specific service, procedure, medication, or referral in order for the service to be covered. Also known as pre-authorization or pre-certification. |
| **Copay** | A fixed out-of-pocket amount a patient pays for a covered healthcare service at the time of the visit, as defined in their insurance plan. The remaining balance is billed to the insurance plan. Copay amounts vary by service type (e.g., primary care vs. specialist vs. emergency). |
| **Deductible** | The amount a patient must pay out-of-pocket for covered health services before their insurance plan begins to pay. For example, with a $1,500 annual deductible, the patient pays the first $1,500 of covered services each plan year before the insurer pays its share. |
| **EOB (Explanation of Benefits)** | A document issued by an insurance plan to a patient after a claim is processed, explaining what services were covered, what the plan paid, and what the patient owes. EOBs are not bills but serve as a financial reconciliation document between the patient, provider, and payer. |
| **FHIR (Fast Healthcare Interoperability Resources)** | A standard for healthcare data exchange developed by HL7 International. FHIR R4 is the current stable release and defines a set of resources (Patient, Appointment, Practitioner, ServiceRequest, etc.) and RESTful APIs for exchanging clinical and administrative health data between systems. |
| **X12 270/271** | Electronic Data Interchange (EDI) transaction sets defined by the ASC X12 standards body and mandated by HIPAA for insurance eligibility inquiries (270) and responses (271). Used by healthcare providers and clearinghouses to verify patient insurance coverage in real time. |
| **Telehealth** | The delivery of healthcare services using telecommunications technology (audio, video, or digital communication tools) that allows patients to receive care remotely without an in-person visit to a clinic. Telehealth services are subject to state-specific licensing and originating site requirements. |
