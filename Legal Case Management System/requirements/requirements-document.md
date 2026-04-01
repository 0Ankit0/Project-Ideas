# Software Requirements Specification — Legal Case Management System

| Field | Value |
|-------|-------|
| **Document Version** | 1.0.0 |
| **Status** | Approved |
| **Date** | 2025-01-15 |
| **Owner** | Product Management — Legal Technology Division |
| **Reviewers** | Engineering Lead, Legal Operations Director, Compliance Officer, Senior Partner Representative |
| **Classification** | Internal — Confidential |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for the Legal Case Management System (LCMS). It serves as the authoritative contract between the product, engineering, and legal operations teams, providing the basis for system design, development, testing, and acceptance. This document governs version 1.0 of the LCMS and will be revised through a formal change-control process for subsequent releases.

### 1.2 Scope

The LCMS is a cloud-hosted, multi-tenant SaaS platform serving mid-to-large law firms (50–1,000+ timekeepers) across multiple practice areas. The system encompasses seven functional domains:

1. **Case & Matter Management** — Full matter lifecycle from intake through archival
2. **Client Management** — Client onboarding, engagement agreements, portal, and relationship history
3. **Document Management** — Version-controlled repository, Bates numbering, privilege log, e-signature, court filing
4. **Time & Billing** — Time entry, LEDES invoicing, IOLTA trust accounting, collections
5. **Court Calendar & Deadlines** — Statute of limitations, procedural deadline calculation, docket management
6. **Task Management** — Precedent checklists, delegation, deadline tracking, calendar integration
7. **Compliance & Security** — Privilege controls, conflicts screening, bar rules, GDPR/CCPA, audit logging

The LCMS does not include: general accounting (replaced by integration), HR management, real estate leasing, or bar association reporting (replaced by data exports to those systems).

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|-----------|
| **Matter** | A single legal engagement or project for a client; synonymous with "case" in litigation contexts |
| **PACER** | Public Access to Court Electronic Records — the federal judiciary's electronic filing and records system |
| **CM-ECF** | Case Management/Electronic Case Files — the federal court e-filing interface accessed through PACER |
| **LEDES** | Legal Electronic Data Exchange Standard — billing file format used for corporate client e-billing |
| **UTBMS** | Uniform Task-Based Management System — standardized billing codes for legal tasks and activities |
| **IOLTA** | Interest on Lawyers' Trust Accounts — trust account program requiring segregated client fund management |
| **Bates Number** | Sequential alphanumeric stamp applied to each page of a document production set for identification |
| **Privilege Log** | An index of documents withheld from production based on attorney-client privilege or work product doctrine |
| **Conflict of Interest** | A situation where the firm's representation of one client may adversely affect another existing or former client |
| **Engagement Letter** | A written agreement between the attorney and client defining the scope of representation and fee arrangements |
| **DocuSign** | Third-party electronic signature platform integrated with the LCMS for document execution |
| **FRCP** | Federal Rules of Civil Procedure — procedural rules governing federal civil litigation |
| **SOL** | Statute of Limitations — the maximum time after an event within which legal proceedings may be initiated |
| **RBAC** | Role-Based Access Control — permission model where access rights are assigned by role |
| **GDPR** | General Data Protection Regulation — EU data privacy law |
| **CCPA** | California Consumer Privacy Act — California state data privacy law |
| **Three-Way Reconciliation** | IOLTA accounting procedure reconciling the firm ledger, client ledger, and bank statement |
| **Timekeeper** | Any firm personnel who records billable or non-billable time (attorneys, paralegals, clerks) |
| **Originating Attorney** | The attorney credited with bringing the client relationship to the firm |
| **Responsible Attorney** | The attorney accountable for the day-to-day management of a matter |

### 1.4 References

- ABA Model Rules of Professional Conduct (2023 edition)
- UTBMS Code Set — Litigation (L-Codes) and Counseling (C-Codes)
- LEDES 1998B File Format Specification
- LEDES 2000 File Format Specification
- Federal Rules of Civil Procedure (effective December 1, 2023)
- PACER CM-ECF Electronic Filing Requirements
- DocuSign eSignature REST API v2.1 Documentation
- GDPR (EU) 2016/679
- California Consumer Privacy Act (Cal. Civ. Code § 1798.100 et seq.)
- IOLTA Program Rules (varies by state bar)

---

## 2. System Overview

### 2.1 System Description

The LCMS is a browser-based SaaS application delivering a unified workspace for all matter-related activity within a law firm. It operates on a microservices architecture deployed in a cloud environment (AWS primary, Azure secondary for disaster recovery). Data is logically partitioned per firm tenant with physical isolation options available for enterprise-tier subscribers. All inter-service communication uses REST APIs internally and event streaming (Apache Kafka) for asynchronous domain events. The system exposes a documented REST and GraphQL API for integration with third-party accounting, CRM, and legal research platforms.

### 2.2 Stakeholders

| Stakeholder | Role in System | Primary Concerns |
|-------------|----------------|-----------------|
| Equity Partners | Matter oversight, billing approval, firm-level reporting | Revenue reporting, client relationship visibility, compliance |
| Associates | Matter work, time entry, document drafting | Ease of time capture, task clarity, deadline visibility |
| Paralegals | Document management, Bates numbering, docket management | Document workflow efficiency, calendar accuracy |
| Legal Assistants | Administrative tasks, scheduling, correspondence | Task management, calendar integration |
| Billing Coordinators | Invoice generation, AR management, trust accounting | LEDES compliance, billing accuracy, collections workflow |
| Client Services | Client onboarding, engagement letters, portal management | Onboarding speed, client communication tools |
| Clients | Matter updates, document access, invoice review and payment | Portal usability, billing transparency, secure communication |
| IT Administrators | System configuration, user management, integrations | Security controls, audit logs, integration health |
| Compliance Officers | Conflicts screening, bar rules, data privacy | Conflict accuracy, audit completeness, GDPR/CCPA compliance |
| Firm Management | Utilization reporting, financial performance, risk management | Dashboards, profitability metrics, risk exposure |

### 2.3 Assumptions

The following assumptions underpin this specification:

1. The firm has a consistent matter numbering convention that will be configured during onboarding.
2. All timekeepers have assigned UTBMS-capable billing rate tables before the system goes live.
3. PACER credentials (one per authorized filer) will be provided by the firm and stored in the LCMS vault.
4. The firm's chart of accounts will be mapped to the LCMS billing and trust accounting modules during implementation.
5. DocuSign business or enterprise plan accounts will be provisioned by the firm.
6. Internet connectivity with a minimum of 10 Mbps per concurrent user is available at all firm locations.
7. The firm uses Microsoft 365 or Google Workspace and has administrative access for SSO configuration.

---

## 3. Functional Requirements

Each requirement is listed with an ID, description, priority (Critical / High / Medium / Low), and source (the stakeholder role or regulatory requirement driving the need).

### 3.1 Case & Matter Management

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-001** | The system shall allow authorized users to create a new matter record by providing: matter name, matter type (litigation, corporate, family, IP, regulatory), responsible attorney, originating attorney, billing partner, client, and billing arrangement. The system shall auto-generate a unique matter number in the firm-configured format upon creation. | Critical | Partners, Associates |
| **FR-002** | Upon creation of a new matter record, the system shall automatically execute a conflict-of-interest check against all existing client records, adverse party records, and related entity records. The check shall return a clear/flag result within 10 seconds. Flagged conflicts shall display the conflicting matter name, client, adverse party, and conflict type. No matter shall be formally opened while a conflict flag is unresolved. | Critical | Compliance Officer, ABA Model Rule 1.7 |
| **FR-003** | The system shall enforce a defined matter lifecycle with the following states: `Intake` → `Active` → `On Hold` → `Closing Review` → `Closed` → `Archived`. Transitions between states shall require authorized user confirmation, and certain transitions (e.g., Active → Closed) shall trigger a closure checklist workflow. | Critical | Firm Management, Partners |
| **FR-004** | The system shall support matter budgeting, allowing a billing partner to define a total budget and phase-level sub-budgets. The system shall calculate real-time budget utilization from approved time entries and disbursements, and send configurable alerts (email and in-app) when utilization reaches 50%, 75%, 90%, and 100% of any phase or total budget. | High | Partners, Billing Coordinators |
| **FR-005** | The system shall support practice-area-specific metadata schemas. Litigation matters shall capture: court name, case number, judge, trial date, and litigation phase. Corporate matters shall capture: transaction type, counterparty, signing authority, and closing date. Family law matters shall capture: family court jurisdiction, case participants, and custody/support status. IP matters shall capture: IP type, USPTO/EPO application number, prosecution stage, and key dates. | High | Associates, Paralegals |
| **FR-006** | The system shall support matter team assignment with defined roles (Responsible Attorney, Billing Partner, Originating Attorney, Associate, Paralegal, Legal Assistant, Expert Witness). Team membership shall determine default document access, task assignment eligibility, and billing rate application. | Critical | All timekeepers |
| **FR-007** | The system shall support linked matter hierarchies, allowing a parent matter to be associated with one or more child matters for clients with subsidiary structures. Billing reports shall support aggregated views across all matters in a hierarchy. | Medium | Partners, Billing Coordinators |
| **FR-008** | The system shall provide a matter closure workflow triggered when a matter transitions to `Closing Review`. The workflow shall require: confirmation that all time entries are billed or written off, final invoice is generated and delivered, all open tasks are closed or transferred, trust funds are disbursed or returned, and a closing memorandum document is filed. Only a user with the Billing Partner or Managing Partner role may approve final closure. | High | Partners, Billing Coordinators |

### 3.2 Client Management

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-009** | The system shall provide a structured client onboarding workflow with the following steps: (1) Intake form collection (contact information, entity type, legal matter description); (2) Identity verification document upload (government ID, articles of incorporation for entities); (3) Conflict check execution; (4) Engagement letter generation and delivery; (5) Signed engagement letter receipt; (6) Fee agreement configuration; (7) Trust account setup (if applicable). Each step shall be tracked and the onboarding record shall show completion status per step. | Critical | Client Services |
| **FR-010** | The system shall generate engagement letters from configurable templates by practice area. Generated letters shall pre-populate client name, matter description, fee arrangement terms, and attorney contact information. Letters shall be delivered via DocuSign for e-signature, and the executed document shall be automatically stored in the matter's document repository upon completion. | Critical | Partners, Client Services |
| **FR-011** | The system shall support configuration of the following fee arrangements per matter: (a) Hourly billing with rate table by timekeeper and matter phase; (b) Fixed fee per phase or per matter; (c) Contingency fee with percentage tiers based on recovery milestone; (d) Retainer with monthly replenishment threshold; (e) Hybrid combinations of the above. Configured fee arrangements shall govern invoice generation logic automatically. | Critical | Billing Coordinators, Partners |
| **FR-012** | The system shall provide a client portal accessible via a secure, authenticated URL distinct from the firm's internal LCMS login. Portal features shall include: active matter list with status; document library (firm-controlled publication); invoice list with online payment capability; and a logged message thread with the matter team. Portal access shall be provisioned per client with configurable permissions. | High | Clients, Client Services |
| **FR-013** | The system shall log all client communications originating within the system (portal messages, email sent from matter records, call notes) in a chronological communication history on the client record, with the author, date/time, communication type, and associated matter. | High | Client Services, Partners |
| **FR-014** | The system shall allow billing coordinators to view trust account balances per client and per matter directly from the client record, with a link to the full trust ledger transaction history. | Critical | Billing Coordinators, IOLTA Rules |

### 3.3 Document Management

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-015** | The system shall maintain a version-controlled document repository per matter. Each document upload shall create a version record containing: version number, upload date/time, uploading user, file size, checksum (SHA-256), and an optional version note. Users shall be able to view version history, download any prior version, and revert the current version to a prior version with an audit entry. Check-out locking shall prevent simultaneous edits by multiple users. | Critical | Paralegals, Associates |
| **FR-016** | The system shall provide a Bates numbering engine that applies sequential alphanumeric stamps to document pages during production. Users shall configure: prefix string (up to 10 characters), zero-padded number length, starting number, and whether to create single or multi-volume production sets. The engine shall support both single-document and bulk Bates stamping across a selected document set. Bates-stamped production sets shall be stored as a separate copy, preserving the original document. | Critical | Paralegals (Litigation) |
| **FR-017** | The system shall provide a privilege log module that allows users to designate documents as privileged (Attorney-Client Privilege, Work Product Doctrine, Joint Defense Privilege, or other configurable basis). The privilege log shall record: document description, date, author, recipient(s), privilege basis, and a non-privileged description suitable for court submission. The log shall be exportable as an Excel spreadsheet and a formatted PDF in standard court submission format. | Critical | Associates, Paralegals (Litigation) |
| **FR-018** | The system shall integrate with DocuSign eSignature API v2.1 to enable document signing workflows directly from matter document records. Users shall be able to: select a document, define signers (from matter contacts or manually entered), set signer sequence (sequential or parallel), configure signing fields, and send the envelope. Status updates (sent, viewed, signed, completed, declined, voided) shall be reflected in real-time via webhook. Completed, executed documents shall be automatically filed back to the matter document repository with a `_EXECUTED` version suffix. | High | Attorneys, Client Services |
| **FR-019** | The system shall integrate with PACER CM-ECF to enable: (a) Electronic filing of documents to federal courts directly from matter records, with filing confirmation number stored against the document; (b) Automated docket retrieval on a configurable schedule (minimum every 4 hours) for active federal matters; (c) Parsing of retrieved docket entries to extract hearing dates, deadlines, and document titles for review and confirmation by an authorized attorney; (d) Storage of retrieved court documents in the matter's document repository. PACER credentials shall be stored encrypted in the system credential vault. | Critical | Paralegals, Associates (Litigation) |
| **FR-020** | The system shall provide full-text search across all documents in the matter repository, supporting: keyword search with Boolean operators (AND, OR, NOT); phrase search with quotation marks; filter by matter, document type, date range, author, and privilege status; and relevance-ranked results with keyword highlighting in document previews. OCR shall be applied to scanned PDF uploads to enable text extraction for search indexing. Search results shall respect the user's matter-level access permissions. | High | All timekeepers |

### 3.4 Time & Billing

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-021** | The system shall provide a time entry interface allowing timekeepers to record time with the following required fields: matter, date, duration (in tenths of an hour, minimum 0.1), UTBMS task code, UTBMS activity code, billing status (Billable / Non-Billable / Pro Bono / No Charge), and narrative description (minimum 10 characters). Optional fields include: phase, disbursement flag, and reference document link. Time entries shall be editable by the entering timekeeper until approved; approved entries shall be locked and require partner authorization to modify. | Critical | All timekeepers, Billing Coordinators |
| **FR-022** | The system shall generate invoices in the following formats: (a) LEDES 1998B — tab-delimited flat file with required fields per the LEDES specification, for corporate clients with e-billing portals; (b) LEDES 2000 — XML format for clients requiring it; (c) Standard PDF invoice with firm letterhead, itemized time and disbursement lines, matter summary, and payment instructions. Invoice generation shall apply the fee arrangement rules configured for the matter (hourly rates, flat fee caps, contingency calculations). | Critical | Billing Coordinators |
| **FR-023** | The system shall provide IOLTA-compliant trust accounting with the following capabilities: (a) Segregated trust ledger per client and per matter; (b) Trust receipts recording client name, matter, amount, deposit date, and source; (c) Disbursements requiring two-party approval (bookkeeper entry + billing partner approval) for amounts above a configurable threshold; (d) Automated three-way reconciliation comparing the firm's trust ledger, individual client ledgers, and the imported bank statement; (e) Trust ledger reports per client and per matter. Firm operating funds shall never commingle with trust funds; the system shall reject any transaction that would cause a negative trust balance for any client. | Critical | Billing Coordinators, Compliance Officer, State Bar Rules |
| **FR-024** | The system shall support an invoice approval workflow with configurable stages: (1) Billing coordinator draft → (2) Responsible attorney review and edit → (3) Billing partner approval → (4) Client delivery. Each stage shall notify the next approver by email. Approved invoices shall be locked. Delivered invoices shall generate an accounts receivable entry. The workflow shall support expedited approval bypass (skipping stages) for partners with appropriate permissions. | High | Billing Coordinators, Partners |
| **FR-025** | The system shall provide accounts receivable aging reports showing outstanding invoice balances by client and matter in 0–30, 31–60, 61–90, and 90+ day buckets, with total firm-wide and partner-level summaries. The system shall support a collections workflow: aged invoices may be flagged for follow-up, assigned to a collections contact, and tracked through states (Outstanding, Follow-Up Sent, Disputed, Payment Plan, Written Off). | High | Billing Coordinators, Partners |
| **FR-026** | The system shall support multi-currency billing for international matters. Each matter may be assigned a billing currency distinct from the firm's base currency. Exchange rates shall be configurable manually or pulled from an integrated exchange rate feed. LEDES invoices for multi-currency matters shall include the billing currency, exchange rate, and base currency equivalent on each line item. | Medium | Billing Coordinators (International Practices) |
| **FR-027** | The system shall maintain billing rate tables with the following dimensions: timekeeper, matter type, client agreement, and effective date range. When a time entry is created, the system shall automatically apply the most specific applicable rate (client-agreement rate > matter-type rate > timekeeper default rate) based on the entry date. Rate changes shall apply prospectively only; historical entries shall retain the rate in effect at the time of entry. | Critical | Billing Coordinators, Partners |

### 3.5 Court Calendar & Deadlines

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-028** | The system shall provide a statute of limitations (SOL) calculator for litigation matters. Users shall select the cause of action type and jurisdiction; the system shall return the applicable limitation period, tolling provisions (minority, discovery rule, fraudulent concealment), and the calculated SOL expiration date based on a user-entered accrual date. The calculation shall generate a documented SOL calculation record filed in the matter, timestamped with the calculating attorney's name and the version of the jurisdiction rule table used. | Critical | Associates, Paralegals (Litigation), Malpractice Risk Management |
| **FR-029** | The system shall compute court procedural deadlines from trigger events using jurisdiction-specific rules. Supported rule sets shall include: FRCP (federal), and the civil procedure rules of all 50 U.S. states. Trigger events shall include: complaint filing date, service of process date, answer filing date, discovery cutoff date, and order issuance date. Deadline calculation shall correctly handle calendar-day vs. business-day rules, court holidays per jurisdiction, and the FRCP Rule 6(a) end-of-period rules. Computed deadlines shall be added to the matter calendar and the responsible attorney's task list automatically. | Critical | Associates, Paralegals (Litigation) |
| **FR-030** | The system shall synchronize federal matter dockets from PACER on a configurable schedule (default: every 4 hours during business hours; once nightly outside business hours). New docket entries retrieved since the last sync shall be presented to the responsible attorney or designated docketing clerk for review and confirmation. Only confirmed docket entries shall be added to the matter's official calendar. The system shall detect hearing dates, order deadlines, and scheduling order entries from docket text using configurable parsing patterns and NLP heuristics. | Critical | Paralegals, Associates (Federal Litigation) |
| **FR-031** | The system shall provide a court calendar module displaying: (a) a single-matter calendar view showing all deadlines, hearings, and tasks; (b) a firm-wide calendar view filterable by practice area, responsible attorney, and court; (c) conflict detection for hearings requiring attorney attendance (flagging when the same attorney has overlapping court appearances); (d) integration with Microsoft 365 Calendar and Google Calendar for bilateral sync of court events. Calendar events shall carry matter reference, event type (Hearing, Deadline, Deposition, Filing Due), and criticality level (Critical, High, Standard). | Critical | All timekeepers |
| **FR-032** | The system shall send multi-channel deadline notifications for court deadlines and statute of limitations expiration dates. Notification lead times shall be configurable at the firm, practice group, and individual timekeeper level. Default lead times shall be: 30 days, 14 days, 7 days, 3 days, and 1 day prior to the deadline. Notifications shall be delivered via: in-app alert, email to the responsible attorney and paralegal, and optional SMS. Acknowledgement of critical deadline notifications shall be required, with escalation to the billing partner if unacknowledged within 4 hours. | Critical | All timekeepers, Malpractice Risk Management |

### 3.6 Task Management

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-033** | The system shall maintain a library of precedent-based task checklists organized by matter type and jurisdiction. When a new matter is opened, the applicable checklist shall be offered for instantiation, automatically computing task due dates relative to configurable matter anchors (e.g., filing date, trial date, closing date). Checklist templates shall be manageable by users with the Practice Group Administrator role. | High | Associates, Paralegals |
| **FR-034** | The system shall support task delegation, allowing a task owner to assign a task to any member of the matter team. Delegated tasks shall appear in the assignee's task dashboard. The delegating user shall receive a notification when the task is marked complete. Incomplete tasks that pass their due date shall be flagged as overdue and shall trigger an escalation notification to the responsible attorney and supervising partner. | High | All timekeepers |
| **FR-035** | The system shall support task dependency chains, where a task may be designated as a predecessor of one or more subsequent tasks. Subsequent tasks shall be automatically unlocked (set to `Available`) only when all predecessor tasks are marked complete. When a task due date changes, the system shall propagate the impact to all downstream dependent tasks and notify the responsible attorney of the net effect on the matter timeline. | Medium | Associates, Paralegals |
| **FR-036** | The system shall integrate with Microsoft 365 (Outlook) and Google Workspace (Gmail) for bidirectional calendar synchronization. Court deadlines, hearing dates, deposition dates, and task due dates created in the LCMS shall appear in the attorney's connected calendar. Events created or modified in the external calendar that match LCMS-tracked matters (by matter reference in the event subject or body) shall generate a prompt to update the corresponding LCMS record. | Medium | All timekeepers |

### 3.7 Compliance & Security

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| **FR-037** | The system shall enforce attorney-client privilege classification on all documents. Each document shall carry a privilege classification field (Not Privileged, Attorney-Client Privileged, Work Product, Joint Defense Privileged, Common Interest, or custom firm-defined classification). Documents classified as privileged shall be accessible only to members of the matter team with attorney status or explicit access grants. Privileged document classification shall be inherited by all subsequent versions of a document. | Critical | Compliance Officer, ABA Model Rule 1.6 |
| **FR-038** | The system shall provide a conflicts-of-interest screening module that maintains a searchable database of all current and former clients, matters, and adverse parties. Prior to opening any new matter, the system shall execute an automated search using the prospective client name and all adverse party names entered during intake. The search algorithm shall account for phonetic similarity, common name variants, and configurable entity-relationship depth (direct, parent, subsidiary, affiliate). Conflict reports shall be generated, signed by the screening attorney, and stored in the matter record. | Critical | Compliance Officer, ABA Model Rules 1.7, 1.9, 1.10 |
| **FR-039** | The system shall process GDPR Article 15 (access), Article 17 (erasure), Article 20 (portability), and CCPA Section 1798.100 (access) and Section 1798.105 (deletion) data subject requests through an automated workflow. Upon receipt of a verified request, the system shall identify all personal data records associated with the requestor across all modules, produce a structured data export (JSON and PDF), and allow the Privacy Officer to execute deletion subject to legal hold override rules. All steps shall be audit-logged with timestamps. GDPR requests shall be fulfilled within 30 calendar days; CCPA requests within 45 calendar days. | High | Compliance Officer, GDPR, CCPA |
| **FR-040** | The system shall implement role-based access control (RBAC) with the following base roles: Managing Partner, Partner, Associate, Paralegal, Legal Assistant, Billing Coordinator, Client Services, IT Administrator, Read-Only Auditor. In addition to role-level permissions, matter-level access overlays shall allow specific users to be excluded from matters they would otherwise have access to by role (e.g., a screened attorney in a conflict situation). Permission changes shall take effect immediately and be audit-logged. | Critical | IT Administrator, Compliance Officer |
| **FR-041** | The system shall maintain an immutable audit log recording every user action that creates, reads (for sensitive data), modifies, or deletes any record in the system, as well as all authentication events (login, logout, failed login, password reset, MFA challenge). Audit log entries shall contain: timestamp (UTC), user ID, user role, action type, affected resource type and ID, IP address, and request ID. The audit log shall be write-only for all application users; only the Read-Only Auditor role can export audit log data. Audit log entries shall be hash-chained to detect tampering. | Critical | Compliance Officer, GDPR Article 30, State Bar Rules |
| **FR-042** | The system shall support data retention schedules configurable per matter type and jurisdiction (e.g., closed litigation matters — 7 years; trust accounting records — state bar minimum, typically 5–7 years). Matters approaching their retention expiration shall trigger a review notification to the designated Records Manager. Legal holds placed on a matter shall override retention schedules and prevent deletion until the hold is formally released by the Compliance Officer. | High | Compliance Officer, Records Manager, State Bar Rules |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement |
|----|-------------|
| **NFR-001** | The system shall return search results for full-text document search queries within 3 seconds for indexes containing up to 5 million documents. |
| **NFR-002** | Matter record load time (including all associated metadata, team, and open task count) shall not exceed 1.5 seconds at the 95th percentile under normal load (up to 500 concurrent users). |
| **NFR-003** | LEDES invoice generation for matters with up to 500 time entries shall complete within 10 seconds. |
| **NFR-004** | Conflict-of-interest check execution shall return results within 10 seconds for databases containing up to 500,000 party records. |
| **NFR-005** | Bates numbering of a 1,000-page document set shall complete within 60 seconds. |

### 4.2 Security

| ID | Requirement |
|----|-------------|
| **NFR-006** | All data in transit shall be encrypted using TLS 1.3 minimum. All data at rest shall be encrypted using AES-256. |
| **NFR-007** | The system shall support multi-factor authentication (MFA) via TOTP (RFC 6238) and FIDO2/WebAuthn. MFA shall be enforceable as mandatory at the firm or role level. |
| **NFR-008** | The system shall support SAML 2.0 and OIDC protocols for enterprise SSO integration with identity providers (Azure AD, Okta, Google Workspace). |
| **NFR-009** | PACER credentials, DocuSign API tokens, and payment processor credentials shall be stored in an encrypted credential vault (AWS Secrets Manager or HashiCorp Vault) and never exposed in application logs or API responses. |
| **NFR-010** | Penetration testing shall be conducted annually by an independent third party. Critical and high findings shall be remediated within 30 and 90 days respectively. |
| **NFR-011** | The system shall implement IP allowlisting and session management controls, including configurable session timeout (default: 30 minutes of inactivity) and single active session enforcement per user (configurable). |

### 4.3 Scalability

| ID | Requirement |
|----|-------------|
| **NFR-012** | The system shall support horizontal scaling of all stateless microservices to handle up to 2,000 concurrent users without performance degradation below NFR-001 through NFR-005 thresholds. |
| **NFR-013** | The document repository shall support storage of up to 50 million documents per tenant without performance degradation. |
| **NFR-014** | Database partitioning and archival strategies shall maintain query performance on the active matter dataset as total matter history grows beyond 1 million closed matters per tenant. |

### 4.4 Availability

| ID | Requirement |
|----|-------------|
| **NFR-015** | The system shall achieve 99.9% uptime (excluding scheduled maintenance) measured monthly, equivalent to a maximum of 43.8 minutes unplanned downtime per month. |
| **NFR-016** | Scheduled maintenance windows shall be conducted between 02:00–05:00 UTC on Sundays, with 72-hour advance notice to firm administrators. |
| **NFR-017** | Recovery Time Objective (RTO) for full system restoration after a major incident: 4 hours. Recovery Point Objective (RPO): 1 hour (using continuous WAL shipping to standby). |
| **NFR-018** | The court calendar and deadline notification subsystem shall have a separate 99.95% uptime SLA, given the critical malpractice-prevention nature of missed deadline alerts. |

### 4.5 Compliance

| ID | Requirement |
|----|-------------|
| **NFR-019** | The system shall maintain SOC 2 Type II certification, with annual audit reports available to clients under NDA. |
| **NFR-020** | The system shall be compliant with GDPR and CCPA, with documented data processing activities and a Data Processing Agreement available for EU-based firm clients. |
| **NFR-021** | All IOLTA trust accounting functionality shall comply with the ABA Model Rules of Professional Conduct Rule 1.15 and the applicable state bar trust accounting rules for all jurisdictions in which the firm is licensed. |

---

## 5. Integration Requirements

| ID | Integration | Requirement |
|----|-------------|-------------|
| **IR-001** | PACER / CM-ECF | The LCMS shall integrate with the PACER CM-ECF API for federal case document filing and docket retrieval. Integration shall use PACER's SOAP-based filing API and REST-based PACER search API. PACER access credentials shall be managed per authorized filer. |
| **IR-002** | DocuSign eSignature | The LCMS shall integrate with the DocuSign eSignature REST API v2.1 for envelope creation, recipient management, signing workflow, and webhook event receipt. The integration shall support embedded signing for client portal users. |
| **IR-003** | LEDES Billing | The LCMS shall generate valid LEDES 1998B and LEDES 2000 formatted billing files for upload to corporate client e-billing portals (TyMetrix 360, Legal Tracker, Passport, Collaborati). No direct API integration is required; file generation and manual upload is the accepted workflow. |
| **IR-004** | Accounting Systems | The LCMS shall export invoice and trust accounting data to QuickBooks Online and NetSuite via their respective REST APIs. Exported data shall include: client, matter reference, invoice number, line items, amounts, payment receipts, and trust transactions. |
| **IR-005** | Microsoft 365 | The LCMS shall integrate with Microsoft 365 via Microsoft Graph API for: (a) SSO via Azure AD; (b) bidirectional calendar sync (Outlook Calendar); (c) email send/receive from matter records using connected attorney mailboxes; (d) Teams notification delivery. |
| **IR-006** | Google Workspace | The LCMS shall integrate with Google Workspace APIs for: (a) SSO via Google OIDC; (b) bidirectional Google Calendar sync; (c) Gmail integration for matter-linked email logging. |
| **IR-007** | Payment Processing | The LCMS client portal shall integrate with Stripe for online invoice payment via ACH and credit card. Payment receipts shall be automatically recorded against the corresponding invoice and, where applicable, as trust account receipts. |
| **IR-008** | Exchange Rate Feed | The LCMS shall integrate with an exchange rate provider (Open Exchange Rates or equivalent) to retrieve daily exchange rates for the 30 most common billing currencies. |

---

## 6. Constraints and Assumptions

### 6.1 Technical Constraints

- The system must be accessible via modern web browsers (Chrome 110+, Firefox 110+, Safari 16+, Edge 110+) without requiring plugin installation.
- The system must not store PACER user passwords in plaintext. Credentials must be encrypted at rest using the system credential vault.
- LEDES file generation must strictly conform to the published LEDES specifications without deviation, as corporate client e-billing portals perform automated validation.
- The privilege log module must not allow bulk declassification of documents. Each document must be individually reviewed and declassified by an attorney with matter access.
- Trust account disbursements above the configurable two-party approval threshold cannot be processed with a single approver, regardless of the approver's seniority.

### 6.2 Business Constraints

- The LCMS must support the firm's existing matter numbering format without requiring firms to change their numbering conventions.
- The system must be able to import matter and client history from legacy case management systems (Clio, MyCase, iManage, ProLaw) via CSV import or API migration tooling provided during onboarding.
- The system must support concurrent operation during the firm's transition from a legacy system, allowing read access to imported legacy matter data while new matters are created in the LCMS.
- All user-facing features must be available in English. Internationalisation (i18n) for other languages is deferred to a future release.

### 6.3 Regulatory Constraints

- IOLTA rules vary by state. The system must allow per-jurisdiction configuration of trust accounting rules rather than enforcing a single national standard.
- The bar rules compliance engine must be configurable per jurisdiction, as ABA Model Rules are adopted with state-specific variations and exceptions.
- Data residency requirements for EU-based firms mean that all personally identifiable information for EU data subjects must be stored in EU-region cloud infrastructure.
- Legal hold functionality must prevent any automated retention-based deletion from executing while a hold is active, including system-level archival jobs.

---

*End of Software Requirements Specification v1.0.0*
