# Requirements Document — Government Services Portal

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Document Title** | Software Requirements Specification — Government Services Portal |
| **Version** | 1.0.0 |
| **Date** | 2024-01-15 |
| **Status** | Approved |
| **Authors** | Priya Thapa (Lead Business Analyst), Rahul Paudel (Solutions Architect), Deepa Karki (Domain SME — e-Governance) |
| **Reviewers** | Arjun Bataju (Engineering Lead), Siddharth Lamichhane (Head of Product), Legal & Compliance Team, Dept. of Electronics and IT (Province) representative |
| **Approval Authority** | Project Steering Committee |
| **Classification** | Internal — Restricted |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Constraints](#5-constraints)
6. [Assumptions and Dependencies](#6-assumptions-and-dependencies)
7. [Operational Policy Addendum](#operational-policy-addendum)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the complete functional and non-functional requirements for the Government Services Portal (GSP) — a unified, citizen-facing digital platform enabling residents to discover, apply for, track, and receive government services entirely online. This document serves as the authoritative reference for design, development, testing, and acceptance of the platform. It is intended for use by the development engineering team, product managers, QA engineers, infrastructure engineers, security auditors, and government department stakeholders.

### 1.2 Scope

The Government Services Portal encompasses the following in-scope components:
- A citizen-facing web portal (Next.js 14) with full mobile-responsive and WCAG 2.1 AA accessibility
- A REST API backend (Django 4.x / DRF) serving all portal functionality
- A workflow engine (Django state machine + Celery) managing application lifecycle
- An integrated payment subsystem supporting ConnectIPS, Razorpay Government, and offline challans
- An encrypted document vault (AWS S3 + KMS)
- A department admin console for field officers, department heads, and super admins
- A grievance redressal module with SLA-enforced escalation
- Multilingual support for 12 Nepali languages plus SMS fallback for low-connectivity areas
- Infrastructure on AWS (ECS Fargate, RDS PostgreSQL, ElastiCache Redis, CloudFront, WAF)

Out of scope for this version:
- Native mobile applications (iOS/Android) — planned for Phase 2
- Integration with municipal corporation local body systems — planned for Phase 3
- AI-based document OCR auto-fill — under evaluation for Phase 2

### 1.3 Definitions, Acronyms, and Abbreviations

| Term / Acronym | Definition |
|----------------|------------|
| **GSP** | Government Services Portal — the system described in this document |
| **Citizen** | A registered individual user of the portal, typically a resident applying for a government service |
| **Department** | A government department or agency offering services through the portal (e.g., Revenue, Municipal, Labour) |
| **NASC (National Identity Management Centre)** | Unique Identification Authority of Nepal — the statutory authority governing NID |
| **NID** | The 12-digit unique identity number issued by NASC (National Identity Management Centre) to Nepali residents |
| **Nepal Document Wallet (NDW)** | Government of Nepal's cloud-based platform for issuance and verification of documents |
| **OTP** | One-Time Password — a time-limited, single-use authentication code |
| **DSC** | Digital Signature Certificate — an electronic signature issued by a licensed Certifying Authority |
| **DRF** | Django REST Framework — the API toolkit used for the GSP backend |
| **SLA** | Service Level Agreement — a contractual commitment on service delivery timeframes |
| **SRS** | Software Requirements Specification — this document |
| **FR** | Functional Requirement |
| **NFR** | Non-Functional Requirement |
| **RBAC** | Role-Based Access Control |
| **KYC** | Know Your Customer — identity verification process |
| **PII** | Personally Identifiable Information |
| **SPD** | Sensitive Personal Data as defined under IT (Amendment) Act 2008 rules |
| **PDPA** | Digital Personal Data Protection Act, 2023 |
| **GFR** | General Financial Rules 2017 — government financial management framework |
| **NIC** | National Informatics Centre — the Government of Nepal IT agency |
| **ConnectIPS** | The official Government of Nepal multi-bank payment gateway |
| **ECS** | Amazon Elastic Container Service |
| **Fargate** | AWS serverless compute engine for containers |
| **RDS** | Amazon Relational Database Service |
| **WAF** | Web Application Firewall |
| **CDN** | Content Delivery Network |
| **JWT** | JSON Web Token — compact, URL-safe token format for authentication |
| **Celery** | Distributed task queue for Python — used for background jobs |
| **WCAG** | Web Content Accessibility Guidelines |
| **RTL** | Right-to-Left text direction (applicable to Urdu) |
| **MFA** | Multi-Factor Authentication |
| **PIR** | Post-Incident Review |

### 1.4 References

| Reference | Description |
|-----------|-------------|
| IT Act 2000 & Amendments | Information Technology Act 2000 and IT (Amendment) Act 2008 |
| NID Act 2016 | NID (Targeted Delivery) Act, 2016 — Sections 8, 29, 33 |
| PDPA 2023 | Digital Personal Data Protection Act, 2023 |
| GFR 2017 | General Financial Rules 2017 — fee collection and financial management |
| CERT-In Directions 2022 | CERT-In Directions on Cyber Incident Reporting, April 2022 |
| WCAG 2.1 | W3C Web Content Accessibility Guidelines, Level AA |
| NIC Security Policy v2.0 | National Informatics Centre Security Guidelines for e-Gov Systems |
| OWASP Top 10 (2021) | Open Web Application Security Project — Top 10 Web Vulnerabilities |
| ConnectIPS Integration Guide | ConnectIPS Merchant Integration Documentation v3.2 |
| NASC (National Identity Management Centre) API Specification | NASC (National Identity Management Centre) Authentication API v2.0 |
| Nepal Document Wallet (NDW) API | Nepal Document Wallet (NDW) Partner API v2.0 |

---

## 2. System Overview

The Government Services Portal is a single, unified digital platform through which citizens can access all government services offered by participating departments in a province or union territory. Citizens authenticate once using NID OTP, Nepal Document Wallet (NDW), email OTP, or SMS OTP, and can then browse the complete service catalog, submit applications, upload required documents, pay fees, track the status of their applications in real time, and receive issued certificates and permits digitally.

Government departments use the portal's admin console to review applications, conduct field verifications, request additional information from citizens, make approval decisions, and generate compliance reports. The platform eliminates the need for citizens to physically visit government offices for routine services.

### Stakeholders

| Stakeholder | Type | Interest |
|-------------|------|----------|
| Citizens | Primary Users | Convenient, fast, transparent access to government services without physical visits |
| Field Officers | Primary Users | Streamlined application review workflow with clear task queues and SLA visibility |
| Department Heads | Primary Users | Operational visibility, SLA compliance, reporting, and service configuration |
| Super Admin | Internal Operators | Platform health, user management, security, audit compliance |
| Auditors | Internal Observers | Compliance reporting, fraud detection, regulatory audit support |
| NASC (National Identity Management Centre) / Nepal Document Wallet (NDW) | External Integrations | Identity verification and document retrieval partner |
| ConnectIPS / Razorpay | External Integrations | Payment collection and settlement |
| AWS | Infrastructure Provider | Hosting, security, managed services |
| NIC / Government IT | External Oversight | Compliance with government IT policies |
| Province Dept. of IT | Sponsoring Authority | Strategic direction and funding |

---

## 3. Functional Requirements

### 3.1 Authentication & Identity (FR-AUTH)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-AUTH-001** | The system shall allow citizens to register using their mobile number verified by SMS OTP. Registration shall capture name, date of birth, mobile number, email address, and preferred language. | Must Have | Citizen Identity |
| **FR-AUTH-002** | The system shall support NID OTP-based identity verification using the NASC (National Identity Management Centre) authentication API (Auth v2.0). The NID number shall be submitted to NASC (National Identity Management Centre) for OTP generation; the portal shall verify the OTP response and store only the masked NID reference (last 4 digits) and NASC (National Identity Management Centre) authentication token. | Must Have | Citizen Identity |
| **FR-AUTH-003** | The system shall support Nepal Document Wallet (NDW) OAuth 2.0 login, allowing citizens to authenticate using their Nepal Document Wallet (NDW) credentials and grant the portal permission to pull linked documents from their Nepal Document Wallet (NDW) storage for pre-filling application forms. | Must Have | Citizen Identity |
| **FR-AUTH-004** | The system shall support email OTP authentication as an alternative login method for citizens who do not have access to NID or Nepal Document Wallet (NDW). Email OTP must be 6 digits, valid for 10 minutes, and invalidated after a single use. | Must Have | Citizen Identity |
| **FR-AUTH-005** | The system shall support SMS OTP authentication as a primary login channel for citizens using feature phones or in areas with low internet connectivity. SMS OTPs must be 6 digits, valid for 10 minutes, and sent via the configured Nepal Telecom / Sparrow SMS gateway (Twilio / CDAC). | Must Have | Citizen Identity |
| **FR-AUTH-006** | The system shall implement JWT-based session management. Access tokens shall expire after 60 minutes; refresh tokens shall expire after 24 hours. Refresh token rotation must be implemented — a used refresh token is immediately invalidated. All active sessions shall be visible to the citizen in their account security settings. | Must Have | Citizen Identity |
| **FR-AUTH-007** | The system shall support optional biometric authentication (fingerprint) for kiosk deployments. The biometric module shall interface with a certified biometric device SDK. Biometric data shall never be transmitted to or stored by the portal; only the authentication assertion (pass/fail) from the SDK shall be received. | Should Have | Citizen Identity |
| **FR-AUTH-008** | The system shall allow citizens to log out from a single session or all active sessions simultaneously. All refresh tokens for the terminated sessions must be immediately invalidated on the server side. | Must Have | Citizen Identity |
| **FR-AUTH-009** | The system shall lock a citizen account after 5 consecutive failed OTP verification attempts within 30 minutes. The lockout duration shall be 30 minutes. The system shall send an account lockout notification to the citizen's registered mobile and email. | Must Have | Citizen Identity |
| **FR-AUTH-010** | The system shall support role assignment at account creation and role modification by Super Admins. Government staff (Field Officers, Department Heads, Auditors) shall authenticate using username/password MFA with TOTP. Citizens shall not use username/password authentication; they must use OTP-based methods only. | Must Have | Citizen Identity |

---

### 3.2 Service Catalog (FR-CATALOG)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-CATALOG-001** | The system shall maintain a structured service catalog with all government services organized by department, category (certificates, permits, licenses, welfare, utilities), and applicant type (individual, business, institution). Each service entry shall include: service name, description, eligibility criteria, required documents list, fee schedule, estimated processing time, SLA, department contact, and applicable language. | Must Have | Service Catalog |
| **FR-CATALOG-002** | The system shall provide a full-text search interface across the service catalog, supporting search by service name, keywords, department name, category, and eligibility criteria. Search results must be returned within 500 ms for 95% of queries. | Must Have | Service Catalog |
| **FR-CATALOG-003** | The system shall allow citizens to filter services by category, department, fee range (free / under रू500 / रू500–रू2,000 / above रू2,000), processing time range, and applicant type. Multiple filters shall be combinable. | Must Have | Service Catalog |
| **FR-CATALOG-004** | The system shall display a detailed service information page for each service, showing: description, eligibility criteria, step-by-step process guide, complete required documents list with accepted formats and size limits, fee schedule with tax breakdown, SLA, FAQs, and a prominently placed "Apply Now" button. | Must Have | Service Catalog |
| **FR-CATALOG-005** | Super Admins shall be able to create, update, and deactivate service entries in the catalog through the Admin Console. Service deactivation shall prevent new applications but not affect in-progress applications. All changes to service catalog entries shall be versioned and logged in the audit trail. | Must Have | Service Catalog |
| **FR-CATALOG-006** | The service catalog shall be cached using Redis with a 15-minute TTL for the public browsing and search views. Cache invalidation shall be triggered automatically on any Super Admin update to the service catalog. | Should Have | Service Catalog |

---

### 3.3 Application Workflow (FR-WORKFLOW)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-WORKFLOW-001** | The system shall implement a configurable state machine for each service application with the following standard provinces: `DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `FIELD_VERIFICATION` → `PENDING_PAYMENT` → `PAYMENT_VERIFIED` → `APPROVED` → `CERTIFICATE_ISSUED`; with alternative terminal provinces: `REJECTED`, `WITHDRAWN`, and `RETURNED_FOR_CORRECTION`. Not every service must use all provinces — state machine configurations shall be service-specific. | Must Have | Workflow Engine |
| **FR-WORKFLOW-002** | The system shall generate a unique application reference number (format: `GSP-{DEPT-CODE}-{YEAR}-{SEQ-8DIGIT}`) for each submitted application. This reference number shall be displayed on all application screens, notifications, and issued documents. | Must Have | Workflow Engine |
| **FR-WORKFLOW-003** | The system shall present multi-step dynamic application forms rendered from a JSON schema stored in the service catalog. Forms shall support: text fields, date pickers, dropdowns, radio buttons, checkboxes, file uploads (PDF/JPG/PNG, max 5 MB per file), address fields with auto-fill, and conditional logic (field visibility based on prior answers). | Must Have | Workflow Engine |
| **FR-WORKFLOW-004** | The system shall allow citizens to save application drafts at any step and resume later. Draft auto-save shall occur every 60 seconds on the frontend. Drafts shall be retained for 30 days before automatic deletion with a 7-day prior notification. | Must Have | Workflow Engine |
| **FR-WORKFLOW-005** | The system shall automatically assign submitted applications to the appropriate Field Officer based on the department's configured assignment rules (round-robin, geographic zone, or manual). If no assignment rule is configured, applications are placed in an unassigned queue visible to all Field Officers in the department. | Must Have | Workflow Engine |
| **FR-WORKFLOW-006** | Field Officers shall be able to update application status to `UNDER_REVIEW`, `FIELD_VERIFICATION`, or `RETURNED_FOR_CORRECTION`. A `RETURNED_FOR_CORRECTION` status transition must include a mandatory written note specifying what the citizen must correct or provide. The citizen shall receive an SMS and email notification with the officer's note. | Must Have | Workflow Engine |
| **FR-WORKFLOW-007** | When an application is returned for correction, the citizen shall be able to edit the specified fields and re-upload documents within a 15-day correction window. After resubmission, the application returns to `UNDER_REVIEW` with a new SLA clock. A maximum of 2 return-for-correction cycles is allowed per application; if the application requires further correction after the second cycle, the Field Officer must escalate to the Department Head for a decision. | Must Have | Workflow Engine |
| **FR-WORKFLOW-008** | Department Heads shall be able to make final approval or rejection decisions. A rejection must include a mandatory written justification. Approved applications shall trigger certificate/permit generation (if applicable) and a payment collection step (if applicable). | Must Have | Workflow Engine |
| **FR-WORKFLOW-009** | The SLA engine shall monitor every active application and compare the current date against the service SLA deadline. At 75% of the SLA period elapsed, a reminder notification shall be sent to the assigned Field Officer. At 100% SLA elapsed, an escalation event shall be raised, notifying the Department Head and recording the breach in the SLA compliance report. | Must Have | Workflow Engine |
| **FR-WORKFLOW-010** | The system shall generate a complete audit timeline for each application showing every status transition, actor, timestamp, and attached notes. This timeline shall be visible to the citizen (in simplified form) and to all department staff with access to the application (in full detail). | Must Have | Workflow Engine |

---

### 3.4 Permits & Licenses (FR-PERMIT)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-PERMIT-001** | The system shall issue digital permits and licenses as PDF documents signed with a valid DSC (Digital Signature Certificate). The signed PDF shall be generated by the backend using a certified DSC signing library and stored in the citizen's document vault with a permanent reference link. | Must Have | Permits & Licenses |
| **FR-PERMIT-002** | Each issued permit shall contain a unique permit number (format: `PRM-{TYPE}-{YEAR}-{SEQ-8DIGIT}`), QR code linking to an online verification page, issuing officer name and designation, department seal, validity dates, and the citizen's name and application reference. | Must Have | Permits & Licenses |
| **FR-PERMIT-003** | The system shall track permit validity periods and send automated renewal reminder notifications to the citizen at 60 days, 30 days, and 7 days before expiry via SMS and email. Reminder notifications shall include a direct link to the renewal application form. | Must Have | Permits & Licenses |
| **FR-PERMIT-004** | The system shall provide a public-facing permit verification endpoint (accessible without login) at which any person can enter a permit number or scan a QR code to verify the permit's authenticity, current status (active/suspended/expired/revoked), and basic details (permit type, holder name, validity). | Must Have | Permits & Licenses |
| **FR-PERMIT-005** | The system shall support permit suspension by Department Heads with a mandatory reason. Suspended permits show a "SUSPENDED" status on the verification page and can be reinstated by the Department Head after the suspension reason is resolved. Citizens shall be notified of suspension and reinstatement. | Must Have | Permits & Licenses |
| **FR-PERMIT-006** | The system shall support permit revocation (permanent cancellation) by Department Heads with a mandatory reason and evidence attachment. Revoked permits cannot be reinstated; the citizen must apply for a fresh permit. Citizens shall be notified of revocation with the reason. | Must Have | Permits & Licenses |
| **FR-PERMIT-007** | The system shall support permit renewal applications, which follow a simplified workflow: the citizen confirms unchanged details or updates required fields, pays the renewal fee, and the department reviews and re-issues with a new validity period. Renewal applications are pre-filled with data from the most recent valid permit. | Must Have | Permits & Licenses |
| **FR-PERMIT-008** | The system shall maintain a complete history of all permits issued, renewed, suspended, and revoked for each citizen's profile, accessible from their document vault. Permit history records shall be retained for 10 years. | Must Have | Permits & Licenses |

---

### 3.5 Fee Payment (FR-PAYMENT)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-PAYMENT-001** | The system shall integrate with the ConnectIPS payment gateway (official Government of Nepal multi-bank payment gateway) for online fee collection. The integration shall support: Net Banking, eSewa/Khalti/ConnectIPS, Debit Card, and Credit Card payment modes. | Must Have | Fee Payment |
| **FR-PAYMENT-002** | The system shall integrate with Razorpay Government as a secondary payment gateway with failover logic — if ConnectIPS returns a gateway error, the citizen shall be offered the option to retry via Razorpay Government without losing their application progress. | Must Have | Fee Payment |
| **FR-PAYMENT-003** | The system shall generate offline payment challans (PDF) for citizens who prefer to pay at authorized bank counters or post offices. The challan shall include the application reference number, citizen name, service name, fee amount, IFSC code, bank account details for government treasury, and a challan validity date (7 days). | Must Have | Fee Payment |
| **FR-PAYMENT-004** | All payment transactions shall be recorded in the portal database with: transaction ID, gateway reference, amount, currency, payment mode, gateway response code, timestamp, and application reference. Payment records shall be immutable after creation. | Must Have | Fee Payment |
| **FR-PAYMENT-005** | The system shall generate a VAT (13%)-compliant payment receipt (PDF) for every successful payment. The receipt shall include: receipt number, date, citizen name, application reference, service name, fee amount, VAT (13%) breakdown (CVAT (13%)/SVAT (13%)/IVAT (13%) as applicable), total amount, and payment mode. Receipts shall be downloadable from the citizen's payment history and emailed automatically upon payment confirmation. | Must Have | Fee Payment |
| **FR-PAYMENT-006** | The system shall handle payment gateway webhooks for asynchronous payment status updates (success, failure, pending). Webhook endpoints shall verify the gateway signature before processing. Payment status changes received via webhook shall update the application status and trigger appropriate notifications within 5 minutes. | Must Have | Fee Payment |
| **FR-PAYMENT-007** | A nightly automated Celery beat task shall run payment reconciliation by comparing the portal's transaction records against the gateway settlement report (downloaded via SFTP or API). Reconciliation discrepancies shall be flagged in the Finance Dashboard and an alert sent to the Super Admin. | Must Have | Fee Payment |
| **FR-PAYMENT-008** | The system shall support fee refund processing triggered by Super Admins or Department Heads for eligible refund scenarios (as defined in the Fee and Payment Policies). Refunds shall be initiated through the payment gateway's refund API and the status tracked until completion. The citizen shall be notified at each stage of the refund process. | Must Have | Fee Payment |

---

### 3.6 Document Vault (FR-DOCS)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-DOCS-001** | The system shall provide each citizen with a personal document vault — a secure, cloud-based storage space — where they can upload, manage, and reuse identity documents (NID, PAN, passport, driving license), qualification certificates, photographs, income documents, and any other documents required by services. | Must Have | Document Vault |
| **FR-DOCS-002** | All documents in the vault shall be stored in AWS S3 with server-side encryption using AWS KMS (SSE-KMS). Each document object shall have a separate KMS data encryption key. S3 bucket policies shall deny all public access. Documents shall only be accessible through pre-signed URLs generated by the backend with a 15-minute expiry. | Must Have | Document Vault |
| **FR-DOCS-003** | All documents uploaded to the vault shall be scanned for malware and viruses using a ClamAV integration triggered as a Celery task immediately after upload. Documents that fail virus scanning shall be quarantined, the citizen notified, and the document marked as unavailable until manually reviewed by the Super Admin. | Must Have | Document Vault |
| **FR-DOCS-004** | Citizens shall be able to tag each document with a type label (e.g., "NID Card", "PAN Card", "Photograph", "Income Certificate") and set a document expiry date where applicable. The system shall send expiry reminder notifications (60-day and 30-day prior) for documents with expiry dates. | Must Have | Document Vault |
| **FR-DOCS-005** | When filling an application form requiring a document, the citizen shall be able to select an existing vault document rather than uploading again. Selected vault documents are attached to the application by reference; the application record stores the vault document ID, not a copy of the file. | Must Have | Document Vault |
| **FR-DOCS-006** | Department staff can access only the documents attached to applications assigned to their department. Department staff shall not have access to the citizen's full document vault. Document access by department staff shall be logged in the audit trail per-document. | Must Have | Document Vault |
| **FR-DOCS-007** | The system shall support Nepal Document Wallet (NDW) document pull — citizens can connect their Nepal Document Wallet (NDW) account and select government-issued documents (NID, driving license, degree certificates) directly from Nepal Document Wallet (NDW) into their vault. Nepal Document Wallet (NDW) documents fetched during a session are cached for the session duration and not permanently stored unless the citizen explicitly saves them to their vault. | Must Have | Document Vault |
| **FR-DOCS-008** | Citizens shall be able to download all documents in their vault as a ZIP archive for personal backup. The export feature shall be rate-limited to 1 full export per 24 hours. Export requests are fulfilled as an asynchronous Celery job with an email notification when the download link is ready. | Should Have | Document Vault |

---

### 3.7 Status Tracking (FR-TRACK)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-TRACK-001** | Citizens shall be able to view a real-time status dashboard for all their submitted applications, showing: application reference number, service name, department, current status, last updated timestamp, assigned officer (first name + department, no contact details), and estimated decision date based on the service SLA. | Must Have | Status Tracking |
| **FR-TRACK-002** | The system shall provide a visual progress stepper on each application's detail page, showing the completed, current, and upcoming workflow states for that application's service type. Each completed step shall show the timestamp and the actor who triggered the transition. | Must Have | Status Tracking |
| **FR-TRACK-003** | Citizens shall receive automated notifications at every application status transition via: in-portal notification (WebSocket push, visible within 30 seconds), SMS to registered mobile number (within 2 minutes), and email to registered email address (within 5 minutes). Notifications shall be in the citizen's preferred language. | Must Have | Status Tracking |
| **FR-TRACK-004** | The system shall provide a public application status lookup tool (no login required) at which anyone can enter an application reference number to see the current status, last update timestamp, and a generic status message. PII fields (citizen name, address) shall not be exposed in the public lookup. | Should Have | Status Tracking |
| **FR-TRACK-005** | The system shall allow citizens to subscribe to WhatsApp Business API notifications for application status updates (in addition to SMS and email), if the citizen opts in during registration or account settings. | Nice to Have | Status Tracking |
| **FR-TRACK-006** | The system shall provide a notification history log in the citizen's account, showing the last 90 days of notifications with delivered/failed status for SMS, email, and in-portal channels. Failed notifications shall show the failure reason and an option for the citizen to manually re-trigger delivery. | Should Have | Status Tracking |

---

### 3.8 Department Admin (FR-ADMIN)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-ADMIN-001** | The Admin Console shall provide each Field Officer with a personalized work queue showing all applications assigned to them, sorted by SLA urgency (most urgent first). The queue shall show application reference, service name, citizen name (masked), submission date, current status, and SLA deadline with a color-coded urgency indicator (green/yellow/red). | Must Have | Dept Admin |
| **FR-ADMIN-002** | Department Heads shall have access to a department dashboard showing: total active applications, applications by status, SLA breach count, average processing time, officer workload distribution, and a list of unassigned applications. Dashboard data must refresh every 5 minutes. | Must Have | Dept Admin |
| **FR-ADMIN-003** | Department Heads shall be able to reassign applications from one Field Officer to another with a mandatory reason note. The reassignment is logged in the application's audit timeline. The new assignee is notified via in-portal notification and email. | Must Have | Dept Admin |
| **FR-ADMIN-004** | Department Heads shall be able to configure service-level settings for their department's services from the Admin Console, including: fee schedule updates (subject to Super Admin approval), document checklist updates, SLA working-days configuration, and officer assignment rules. | Must Have | Dept Admin |
| **FR-ADMIN-005** | The Admin Console shall allow Field Officers to communicate with citizens through an in-portal messaging system tied to the application record. Messages are logged, visible to both parties and to department supervisors, and trigger an email notification to the recipient. Direct phone numbers or personal email addresses shall not be shared through this channel. | Must Have | Dept Admin |
| **FR-ADMIN-006** | Super Admins shall be able to create, edit, and deactivate departments, department staff accounts, and service catalog entries through the Admin Console. All Super Admin actions are logged with a timestamp and reason field in the audit trail. | Must Have | Dept Admin |
| **FR-ADMIN-007** | The Admin Console shall provide exportable reports for: applications received by service/date range, average processing time by service/officer, SLA compliance rate, payment reconciliation summary, grievance resolution rate, and department staff activity. Reports are exportable in CSV and PDF formats. | Must Have | Dept Admin |
| **FR-ADMIN-008** | Auditors shall have a read-only audit log viewer in the Admin Console, filterable by: date range, user ID, event type (login, data access, status change, payment, export), department, service, and IP address. The audit log viewer supports pagination (100 records per page) and CSV export. | Must Have | Dept Admin |

---

### 3.9 Grievance Redressal (FR-GRIEVANCE)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-GRIEVANCE-001** | Citizens shall be able to file a grievance against any submitted application by selecting the application and clicking "File Grievance". The grievance form must capture: grievance category (delay, incorrect rejection, officer misconduct, technical issue, other), a written description (minimum 50 characters), and optional supporting evidence upload (PDF/image, max 10 MB). | Must Have | Grievance |
| **FR-GRIEVANCE-002** | Upon grievance submission, the system shall generate a unique grievance reference number (format: `GRV-{DEPT}-{YEAR}-{SEQ-6DIGIT}`), auto-assign it to the responsible department's grievance queue, and send the citizen an acknowledgement SMS and email within 30 minutes. | Must Have | Grievance |
| **FR-GRIEVANCE-003** | Grievances shall follow an SLA-enforced escalation path: Level 1 (Field Officer, 3 working days), Level 2 (Department Head, 7 working days from filing), Level 3 (Commissioner-level officer, 15 working days from filing). Automatic escalation shall be triggered by Celery beat tasks at each SLA threshold. Citizens shall be notified of each escalation. | Must Have | Grievance |
| **FR-GRIEVANCE-004** | The assigned officer must provide a substantive written resolution response before marking a grievance as resolved. The citizen shall be notified of the resolution with the written response. Citizens have 5 working days after a resolution to accept it or appeal. If no response is received within 5 days, the grievance is auto-closed in favour of the department's resolution. | Must Have | Grievance |
| **FR-GRIEVANCE-005** | Citizens who are dissatisfied with the resolution may file an appeal. Appeals are escalated to the next level in the escalation path. A maximum of 2 appeal levels are supported. Second-level appeals (Level 3 unresolved) are flagged for the Super Admin's attention and tracked separately. | Must Have | Grievance |
| **FR-GRIEVANCE-006** | The grievance module shall provide analytics to the Super Admin showing: total grievances filed by department/category, resolution rate by SLA tier, average resolution time, repeat grievances by citizen (potential misuse detection), and monthly trend charts. | Must Have | Grievance |

---

### 3.10 Accessibility & Multilingual (FR-ACCESS)

| ID | Requirement | Priority | Module |
|----|-------------|----------|--------|
| **FR-ACCESS-001** | The citizen portal frontend shall comply with WCAG 2.1 Level AA across all citizen-facing pages. This includes: minimum 4.5:1 colour contrast ratio for normal text, 3:1 for large text; full keyboard operability with visible focus indicators; ARIA labels on all interactive elements; alt text on all non-decorative images; and page titles reflecting the current page context. | Must Have | Accessibility |
| **FR-ACCESS-002** | The portal shall support 12 Nepali languages: English, Hindi, Bengali, Telugu, Tamil, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi, and Urdu. All UI strings (labels, buttons, messages, form field names, error messages) shall be translatable from a centrally managed language bundle. Translations shall be maintained by the Super Admin in the Admin Console. | Must Have | Accessibility |
| **FR-ACCESS-003** | The Urdu language interface shall render fully in RTL (right-to-left) text direction. The Next.js frontend shall use CSS logical properties and a dynamic `dir="rtl"` attribute on the `<html>` element for RTL languages, ensuring correct layout mirroring. | Must Have | Accessibility |
| **FR-ACCESS-004** | SMS notifications shall be delivered in the citizen's preferred language (as set during registration or in account settings). For languages using non-Latin scripts (Hindi, Telugu, Tamil, etc.), SMS messages shall be encoded in Unicode (UCS-2) to preserve the original script. The Nepal Telecom / Sparrow SMS gateway configuration shall support Unicode message delivery. | Must Have | Accessibility |
| **FR-ACCESS-005** | The system shall provide an SMS-based service interface for citizens without smartphone or internet access. Citizens can send SMS commands to the portal's dedicated SMS number to: check application status (`STATUS <ref-number>`), receive challan payment details (`CHALLAN <ref-number>`), check permit validity (`PERMIT <permit-number>`), and request a callback from a department officer (`HELP <ref-number>`). Responses are delivered as SMS messages in the citizen's preferred language. | Should Have | Accessibility |
| **FR-ACCESS-006** | The portal shall include an accessibility statement page (conforming to WAI model) listing: the conformance level, any known accessibility gaps with planned remediation dates, the date of last accessibility audit, and contact information for reporting accessibility issues. Automated axe-core accessibility scans shall run on every CI pipeline build and fail the build on any WCAG 2.1 AA violation. | Should Have | Accessibility |

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements (NFR-PERF)

| ID | Requirement | Priority |
|----|-------------|----------|
| **NFR-PERF-001** | All citizen-facing API endpoints must respond within 500 ms at the 95th percentile (p95) under normal load defined as 5,000 concurrent users. Document upload endpoints must respond within 3,000 ms at p95. These SLAs must be maintained without degradation during horizontal scaling events. | Must Have |
| **NFR-PERF-002** | The portal home page, service catalog listing, and application status page must achieve a Largest Contentful Paint (LCP) under 2.5 seconds and a Cumulative Layout Shift (CLS) below 0.1 as measured by Google Lighthouse on a simulated 4G mobile connection. Core Web Vitals must be monitored continuously via Real User Monitoring (RUM). | Must Have |
| **NFR-PERF-003** | The system must support a peak load of 50,000 concurrent users during high-demand events (e.g., scheme enrollment deadlines, permit renewal rushes) without API error rates exceeding 0.1%. Load testing using Locust shall be performed against a production-equivalent environment before go-live and quarterly thereafter. | Must Have |
| **NFR-PERF-004** | Database query execution time must not exceed 100 ms for 99% of queries under normal load. All frequently accessed queries must be covered by appropriate PostgreSQL indexes. Query performance must be monitored via pg_stat_statements and alerts raised when average query time for any query exceeds 200 ms. | Must Have |
| **NFR-PERF-005** | Redis cache hit rate for service catalog and application status queries must be maintained above 85%. Cache eviction policies shall be configured to prevent memory exhaustion from causing degraded performance. Redis memory usage must be monitored with a CloudWatch alert at 80% utilization. | Should Have |
| **NFR-PERF-006** | Celery background tasks must not exhibit task queue depth exceeding 500 pending tasks during normal operation. Celery worker auto-scaling (via ECS Fargate task scaling based on Redis queue depth) must bring the queue depth below 500 within 5 minutes of a spike. | Should Have |

---

### 4.2 Security Requirements (NFR-SEC)

| ID | Requirement | Priority |
|----|-------------|----------|
| **NFR-SEC-001** | All data in transit between clients and the portal (browser, Nepal Telecom / Sparrow SMS gateway, payment gateways, Nepal Document Wallet (NDW), NASC (National Identity Management Centre)) must be encrypted using TLS 1.3. TLS 1.0 and 1.1 must be disabled. Cipher suites must be restricted to those listed in NIST SP 800-52 Rev. 2. | Must Have |
| **NFR-SEC-002** | All Sensitive Personal Data (SPD) fields stored in PostgreSQL (NID masked reference, PAN number, date of birth, income data) must be encrypted at the column level using Django's field-level encryption library (e.g., `django-cryptography`) with AES-256-GCM. Encryption keys must be stored in AWS KMS, not in the application configuration. | Must Have |
| **NFR-SEC-003** | The portal must be protected by AWS WAF with the following managed rule groups enabled: AWS Managed Rules Common Rule Set, AWS Managed Rules Known Bad Inputs Rule Set, AWS Managed Rules SQL Database Rule Set, and a custom rate-limiting rule capping requests at 100/second per IP. | Must Have |
| **NFR-SEC-004** | All API endpoints must implement JWT authentication and authorization. Authorization must be checked at the DRF permission layer using role-based permission classes. No security-sensitive logic shall be performed solely on the frontend. | Must Have |
| **NFR-SEC-005** | A third-party penetration test must be conducted annually by a CERT-In empanelled security auditor. Critical and high findings must be remediated within 30 days of the penetration test report. Medium findings must be remediated within 90 days. All findings and remediation actions must be documented. | Must Have |
| **NFR-SEC-006** | All production secrets (database credentials, API keys, KMS key IDs, JWT secrets) must be stored in AWS Secrets Manager. No secrets shall be hardcoded in source code, committed to version control, or stored in environment variables in container task definitions as plain text. | Must Have |
| **NFR-SEC-007** | The system must implement Content Security Policy (CSP), HTTP Strict Transport Security (HSTS with preloading, min-age 31536000), X-Content-Type-Options, X-Frame-Options (DENY), and Referrer-Policy headers on all responses. These headers must be verified in the CI pipeline using the Mozilla Observatory scanner. | Must Have |
| **NFR-SEC-008** | An immutable audit log must capture every security-relevant event: authentication attempts (success/failure), OTP generation and verification, token refresh and revocation, document access, payment initiation and completion, admin actions, role changes, and data exports. Audit log records must be written to a separate append-only PostgreSQL schema with restricted write permissions. | Must Have |

---

### 4.3 Availability Requirements (NFR-AVAIL)

| ID | Requirement | Priority |
|----|-------------|----------|
| **NFR-AVAIL-001** | The production portal must achieve 99.9% monthly availability, excluding approved maintenance windows. Availability is measured as the percentage of time all citizen-facing API endpoints return 2xx or 3xx responses, as monitored by CloudWatch Synthetic Canaries. | Must Have |
| **NFR-AVAIL-002** | The RTO (Recovery Time Objective) for a full primary-region failure must be 4 hours or less. The RPO (Recovery Point Objective) must be 1 hour or less. DR failover capability must be validated by a full-scale DR drill at least once per quarter, with drill results documented. | Must Have |
| **NFR-AVAIL-003** | Scheduled maintenance must be performed during the approved maintenance window (Sundays 02:00–06:00 IST) with a minimum 48-hour advance notification to citizens via portal banner, SMS, and email. Emergency maintenance outside this window requires documented post-incident review. | Must Have |
| **NFR-AVAIL-004** | Deployments must use a rolling update strategy on ECS Fargate with zero citizen-visible downtime. At least 2 tasks per service must remain healthy during a deployment. Deployment health checks must verify API health before completing the rollout; automatic rollback must be triggered if >5% of health checks fail during deployment. | Must Have |

---

### 4.4 Scalability Requirements (NFR-SCALE)

| ID | Requirement | Priority |
|----|-------------|----------|
| **NFR-SCALE-001** | The ECS Fargate service must scale out automatically from a baseline of 2 tasks to a maximum of 50 tasks based on CPU utilization (scale-out at 70%) and request count (scale-out at 1,000 requests/minute per task). Scale-out must complete within 3 minutes of the trigger threshold being reached. | Must Have |
| **NFR-SCALE-002** | The RDS PostgreSQL instance must support horizontal read scaling via up to 3 read replicas. The Django application must route read-only queries (catalog browsing, status lookups, report generation) to read replicas through the database router. Write operations (application submissions, payment records, audit log entries) must always route to the primary instance. | Must Have |
| **NFR-SCALE-003** | The document storage subsystem (AWS S3) must support unlimited storage growth without performance degradation. S3 lifecycle policies must be configured to transition documents older than 5 years to S3 Glacier Instant Retrieval, with a retrieval SLA of 24 hours for archived documents. | Should Have |
| **NFR-SCALE-004** | The Celery worker fleet must auto-scale based on Redis queue depth. A CloudWatch alarm must trigger ECS scaling for the Celery worker task definition when queue depth exceeds 200 tasks, scaling to a maximum of 20 worker tasks. | Should Have |

---

### 4.5 Compliance Requirements (NFR-COMPLY)

| ID | Requirement | Priority |
|----|-------------|----------|
| **NFR-COMPLY-001** | The system must comply with the NID (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016, specifically Sections 8 (authentication), 29 (no storage of NID number beyond necessity), and 32 (privacy of information). NASC (National Identity Management Centre) Authentication API must be used for all NID-based authentication. | Must Have |
| **NFR-COMPLY-002** | The system must comply with the Digital Personal Data Protection Act (PDPA) 2023, including: obtaining and recording explicit consent before data collection, providing citizens with the right to access and erase their data, notifying affected citizens and the Data Protection Board within 72 hours of a personal data breach. | Must Have |
| **NFR-COMPLY-003** | The system must comply with the Information Technology Act 2000 and associated rules. All SPD (Sensitive Personal Data) must be protected under IT (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules 2011. | Must Have |
| **NFR-COMPLY-004** | The portal must be certified under the Government of Nepal's GIGW (Guidelines for Nepali Government Websites) v3.0, including WCAG 2.1 AA accessibility, multilingual support, and mobile-first design. GIGW compliance certification must be obtained before go-live. | Must Have |
| **NFR-COMPLY-005** | All financial transactions must comply with GFR (General Financial Rules) 2017 Chapter 6 on receipts and payments. Payment receipts must be VAT (13%)-compliant invoices. Reconciliation must be performed daily and records retained for 7 years. | Must Have |
| **NFR-COMPLY-006** | Penetration testing must be performed by a CERT-In empanelled auditor annually. Vulnerability Assessment must be performed quarterly. VAPT reports must be submitted to the relevant government IT authority. All critical vulnerabilities must be patched within 30 days of discovery. | Must Have |

---

## 5. Constraints

### 5.1 Technical Constraints

- **Authentication Integration**: All NID-based authentication must be performed exclusively through the NASC (National Identity Management Centre)'s official API. The portal cannot implement its own NID OTP mechanism. NASC (National Identity Management Centre) API availability and rate limits impose a constraint on the NID authentication throughput.
- **Nepal Document Wallet (NDW) OAuth**: Nepal Document Wallet (NDW) integration is subject to the terms of the Nepal Document Wallet (NDW) Partner Program. API access is limited to document types approved under the partnership agreement. Pull of documents is only possible with real-time citizen consent during an authenticated session.
- **ConnectIPS Dependency**: ConnectIPS is the primary government payment gateway and must be the first payment option presented. Any other payment gateway must be presented as a secondary option. ConnectIPS's rate limits (max 10,000 transactions per hour) must be considered in capacity planning.
- **SMS Gateway Reliability**: Delivery rates for Nepali Nepal Telecom / Sparrow SMS gateways to mobile numbers in remote or low-connectivity areas may be lower than 90%. The system cannot guarantee SMS delivery; the portal must function even if the citizen does not receive an SMS notification.
- **DSC Signing Infrastructure**: Digital Signature Certificate signing requires access to a Hardware Security Module (HSM) or certified DSC signing service. The DSC certificate must be renewed before expiry; an expiry monitoring alert must be in place.

### 5.2 Regulatory Constraints

- NID numbers must never be stored in the portal database beyond the authentication session; only the NASC (National Identity Management Centre)-issued authentication reference token and a masked representation (last 4 digits) are permissible.
- Any service that collects biometric data (fingerprint, iris) must comply with NASC (National Identity Management Centre)'s Biometric Data Policy and must not retain raw biometric data.
- The portal must comply with government procurement policies; all third-party vendor contracts must be approved by the relevant government authority.
- Payment gateway integrations must use only payment gateways empanelled by the Government of Nepal/Province Treasury.

### 5.3 Budget and Timeline Constraints

- The platform must be delivered in phases, with the core citizen-facing functionality (Auth, Service Catalog, Workflow, Payment, Document Vault) operational within 12 months of project kick-off.
- Infrastructure costs must be optimized to remain within the approved annual IT budget; over-provisioned ECS tasks must be scaled down during non-peak hours using ECS scheduled scaling.
- Open-source components must be used wherever possible to reduce licensing costs, subject to security vetting.

---

## 6. Assumptions and Dependencies

### 6.1 Assumptions

- Citizens registered for NID OTP authentication are assumed to have an active mobile number linked to their NID in the NASC (National Identity Management Centre) database.
- Government department staff (Field Officers, Department Heads) are assumed to have reliable internet connectivity and standard modern web browsers (Chrome 100+, Firefox 100+, Edge 100+, Safari 15+).
- The Nepal Document Wallet (NDW) Partner Agreement will be in place before the portal goes live; without this, Nepal Document Wallet (NDW) integration will be unavailable and citizens will rely on manual document upload.
- ConnectIPS sandbox credentials are available for development and QA testing; production credentials require a formal government entity onboarding process.
- The province government's IT department will provide the DSC certificate for permit signing; the portal team is not responsible for obtaining the DSC.
- Departments will provide finalized service configurations (fee schedules, document checklists, SLAs, officer assignments) at least 4 weeks before their service goes live on the portal.
- Translations for all 12 languages will be provided by a certified translation agency engaged by the government; the portal team is responsible only for the translation management system.

### 6.2 Dependencies

| Dependency | Description | Owner | Risk if Delayed |
|------------|-------------|-------|-----------------|
| NASC (National Identity Management Centre) API Access | Production credentials for NID Auth v2.0 API | NASC (National Identity Management Centre) / Government IT | NID OTP login unavailable at go-live |
| Nepal Document Wallet (NDW) Partnership | Nepal Document Wallet (NDW) Partner API access approval | NIC / Nepal Document Wallet (NDW) Team | Document pull unavailable; citizens must upload manually |
| ConnectIPS Onboarding | Government entity registration with ConnectIPS | Finance Department | Online payment unavailable; challan-only fallback |
| DSC Certificate | Digital Signature Certificate for permit PDF signing | Province IT / NICSI | Permits cannot be digitally signed |
| AWS Account Setup | Production AWS account with NIC-compliant VPC setup | DevOps / Cloud Team | Deployment delayed |
| SMS Gateway Contract | CDAC/Twilio Nepal Telecom / Sparrow SMS gateway contract with government DLT registration | Procurement Team | SMS notifications unavailable at go-live |
| Department Data | Service catalog entries, fee schedules, SLA configurations per department | Each Department's Nodal Officer | Incomplete service catalog at launch |
| Translations | Certified translations for all UI strings in 12 languages | Translation Agency | Multilingual support delayed |

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policies

**CDP-001 — NID Data Minimisation**
In compliance with Section 29 of the NID Act 2016, the portal does not store the full 12-digit NID number at any point. During authentication, the citizen enters their NID number in the browser; this number is transmitted directly to the NASC (National Identity Management Centre) authentication API over TLS without being logged or stored by the portal backend. The portal stores only the NASC (National Identity Management Centre)-issued authentication transaction ID and the last 4 digits of the NID number (masked display reference). This data is stored encrypted at rest using AES-256-GCM with keys managed in AWS KMS.

**CDP-002 — Consent Management**
Under the PDPA 2023, citizen consent must be freely given, specific, informed, and unambiguous before processing personal data. The portal implements a consent management screen during first registration and before each application submission, presenting the specific data being collected, the purpose, the retention period, and the sharing recipients (department, payment gateway, identity authority). Consent records are stored in the `citizen_consents` table with: citizen ID, consent version, consent text hash, timestamp, IP address, and user-agent. Citizens can withdraw consent from the Account Settings screen; withdrawal triggers a data deletion request workflow.

**CDP-003 — Data Breach Response**
In the event of a data breach involving SPD, the following response procedure applies: (1) Incident detection and containment within 1 hour; (2) Impact assessment (which citizens affected, data type, extent of exposure) within 3 hours; (3) CERT-In notification within 6 hours of detection per CERT-In Directions (April 2022); (4) Notification to affected citizens within 72 hours via SMS and email with clear description of the breach, data affected, risks, and remediation steps; (5) Post-incident review and detailed report to the Data Protection Board within 72 hours per PDPA 2023; (6) Full PIR documented within 5 business days.

**CDP-004 — Data Localisation**
All citizen personal data (profiles, application records, payment records, audit logs) must be stored in AWS data centres located in Nepal (ap-south-1, Mumbai as primary; ap-southeast-1, Singapore as DR region). Any data stored or replicated to Singapore for DR purposes must be covered under a cross-border transfer mechanism compliant with PDPA 2023 provisions. Document uploads in S3 are stored in the ap-south-1 region primary; cross-region replication to ap-southeast-1 is encrypted in transit and at rest.

**CDP-005 — Staff Access Controls**
Access to citizen personal data by portal operations staff (DevOps, Support) is governed by the Principle of Least Privilege. Production database access requires approval via an access request workflow, is time-limited (max 4-hour session), is fully audited, and is reviewed monthly by the Super Admin. No staff member shall access citizen personal data for purposes other than resolving a support incident; all such accesses are logged with the associated support ticket number.

---

### 2. Service Delivery SLA Policies

**SLA-001 — Portal Availability and Measurement**
The portal availability SLA is 99.9% per calendar month, corresponding to a maximum of 43.8 minutes downtime per month. Availability is measured as the proportion of one-minute intervals in which CloudWatch Synthetic Canaries successfully receive a 2xx response from the `/api/v1/health/` endpoint for at least 1 of 2 monitoring canaries in different AWS availability zones. The monthly availability percentage is published on the Portal Status Page accessible at `status.govportal.gov.in`. Availability data is retained for 13 months.

**SLA-002 — API Performance Monitoring**
API response time SLAs (p95 ≤ 500 ms for regular endpoints, p95 ≤ 3,000 ms for document endpoints) are monitored via AWS CloudWatch Container Insights and X-Ray distributed tracing. A CloudWatch alarm triggers an alert to the on-call engineer when p95 exceeds the threshold for 5 consecutive minutes. Performance degradation not attributable to external dependency (NASC (National Identity Management Centre), ConnectIPS) is classified as a P2 incident. Monthly performance reports are generated and reviewed by the Engineering Lead.

**SLA-003 — Application Processing SLA Enforcement**
The workflow engine SLA monitor (Celery beat task, runs every 15 minutes) checks all active applications and computes the elapsed percentage of the service SLA. Notifications and escalations are triggered at 75% and 100% SLA elapsed. SLA compliance data is stored in the `application_sla_events` table. The department dashboard shows real-time SLA compliance metrics. Monthly SLA compliance reports are reviewed by Department Heads and the Programme Director. Persistent SLA breach rates above 10% in a department trigger a formal service review.

**SLA-004 — Notification Delivery Monitoring**
All notification events are logged to the `notification_log` table with delivery status. An alert is raised to the Super Admin if the SMS delivery failure rate exceeds 10% over a 1-hour window. Email delivery failures are monitored via the email service provider's webhook. Persistent notification failures trigger a vendor escalation. Citizens can manually re-request any failed notification from their notification history.

---

### 3. Fee and Payment Policies

**FEE-001 — Fee Freeze on Submission**
The fee amount applicable to an application is locked (frozen) at the time the citizen submits the application (state transitions from `DRAFT` to `SUBMITTED`). Subsequent fee schedule changes do not affect in-progress applications. This is implemented by storing the fee amount and schedule version in the `application_fee` record at submission time. Fee freeze protects citizens from unexpected cost increases during processing.

**FEE-002 — Challan Expiry Automation**
The Celery beat task `expire_challans` runs daily at 00:30 IST and marks challans older than 7 days as `EXPIRED`. Expired challans are not usable for payment; the associated application returns to `DRAFT` with a `CHALLAN_EXPIRED` flag. The citizen is notified and directed to regenerate the challan. The challan generation endpoint validates that the associated application is in an eligible province before generating a new challan.

**FEE-003 — Duplicate Payment Detection**
The payment module implements idempotency for payment creation requests using a client-generated idempotency key. If the portal receives a payment initiation request for an application that already has a successful payment record, the request is rejected with a `409 Conflict` response. The duplicate payment detection logic also runs during the nightly reconciliation to identify and flag any duplicate settlement credits from the payment gateway.

**FEE-004 — Refund Tracking and Audit**
All refund requests are tracked in the `payment_refund` table with: original payment ID, refund reason, requested by (admin user ID), requested at timestamp, gateway refund reference, refund status, and completion timestamp. Refund audit records are immutable. Monthly refund reports (total refunds by service, refund rate, refund amounts) are available to the Super Admin and Finance Officer.

---

### 4. System Availability Policies

**AVAIL-001 — Change Management**
All production changes (code deployments, configuration changes, infrastructure changes) must go through a change approval process: (a) change request raised in the ticketing system with impact assessment; (b) reviewed and approved by Engineering Lead and Super Admin; (c) tested in a production-equivalent staging environment; (d) deployed during the approved maintenance window unless classified as an emergency change. Emergency changes (critical security patches, active incident response) may be deployed outside the window with immediate notification and a mandatory post-change review within 24 hours.

**AVAIL-002 — Capacity Planning**
Quarterly capacity reviews are conducted by the DevOps team reviewing: average and peak CPU/memory utilization of ECS tasks, RDS instance metrics (CPU, IOPS, connections), ElastiCache memory usage, S3 storage growth rate, and CloudFront data transfer. ECS task sizing and RDS instance classes are adjusted before projected demand increases (e.g., ahead of scheme enrollment periods). Auto-scaling configurations are reviewed and tested during each capacity review.

**AVAIL-003 — Incident Management**
All production incidents are tracked in PagerDuty. The on-call rotation covers 24×7 with a primary and secondary on-call engineer. P1 incidents require a response within 5 minutes (engineer on bridge call within 10 minutes). P2 incidents require a response within 15 minutes. All P1 and P2 incidents require a Post-Incident Review (PIR) document published to the internal wiki within 5 business days, covering: timeline, root cause, impact, remediation steps, and follow-up action items.

**AVAIL-004 — Business Continuity**
In a scenario where both the primary region (Mumbai) and DR region (Singapore) are simultaneously unavailable, the Business Continuity Plan activates a static fallback mode: the portal displays a static HTML page with department contact numbers and offline service instructions, served from a pre-configured S3 static website with a separate DNS CNAME. This fallback is tested annually. The Business Continuity Plan is reviewed and updated annually by the Project Steering Committee.
