# Insurance Management System — Requirements Document

**Project:** P&C Insurance SaaS Platform
**Version:** 1.0
**Status:** Draft
**Domain:** Property & Casualty Insurance

---

## Executive Summary

This document defines the functional, non-functional, regulatory, and integration requirements for a cloud-native Property & Casualty (P&C) Insurance Management SaaS platform. The platform supports the full insurance value chain — from broker-initiated policy applications and automated underwriting decisioning through claims adjudication, premium billing, reinsurance cession, and NAIC regulatory reporting.

The system is designed to serve admitted and non-admitted carriers operating across multiple U.S. states, supporting personal lines (auto, homeowners, renters) and commercial lines (BOP, general liability, workers' compensation, commercial auto). It provides a multi-tenant architecture enabling insurers, MGAs, and program administrators to configure rate tables, coverage rules, and compliance workflows independently without code changes.

Key business drivers include reducing manual underwriting cycle time by 60%, automating claims FNOL triage, enabling real-time reinsurance bordereaux submission, and producing state-mandated filings with zero manual intervention. The platform must meet SOC 2 Type II, PCI-DSS Level 1, and all applicable NAIC model law requirements.

---

## Scope

### In-Scope

- Policy lifecycle management: application, quote, bind, issue, endorse, renew, cancel, reinstate
- Automated and manual underwriting with configurable rules engines and risk scoring
- First Notice of Loss (FNOL) intake, claims investigation workflows, reserves management, and settlement processing
- Premium billing with installment plans, payment processing, notices, and collections
- Facultative and treaty reinsurance cession tracking, bordereau generation, and recoveries
- Broker and agent portal with binding authority, commission tracking, and submission management
- Regulatory reporting: NAIC statutory filings, state-mandated forms, SERFF integration, annual statement preparation
- Role-based access control, audit trails, and compliance dashboards
- Integration with ISO/AAIS rating bureaus, state DMV databases, LexisNexis, credit bureaus, and payment gateways
- Multi-state, multi-line-of-business configuration with jurisdiction-aware rules

### Out-of-Scope

- Life, health, or annuity product lines
- Actuarial reserving models and loss development triangle calculations (these are read-only imports)
- Direct-to-consumer (DTC) policyholder acquisition marketing
- Core financial accounting and general ledger (platform produces journals consumed by external ERP)
- Claims litigation management and legal case tracking beyond initial referral
- Third-party administrator (TPA) operational management
- International or surplus lines rated outside U.S. jurisdictions in v1.0

---

## Stakeholders

| Stakeholder | Role | Key Concerns |
|---|---|---|
| Policyholder | Insured individual or business entity | Easy self-service, fast claims, transparent billing, digital policy documents |
| Insurance Broker / Agent | Distributor who submits applications and binds coverage | Submission speed, binding authority limits, commission visibility, real-time quoting |
| Underwriter | Evaluates risk and approves or declines coverage | Rules engine accuracy, referral queue management, risk score transparency, override audit |
| Claims Adjuster | Investigates and settles claims | FNOL completeness, reserve adequacy, document management, payment workflows |
| Actuary | Analyzes loss experience and sets rates | Data export quality, loss ratio reporting, exposure aggregation, reinsurance recoverable accuracy |
| Reinsurance Manager | Manages cession agreements and recoveries | Bordereaux accuracy, treaty limits tracking, recoverable aging, cash call processing |
| Compliance Officer | Ensures adherence to state and federal regulations | Filing deadlines, form version control, audit logs, NAIC submission status |
| IT / Platform Administrator | Manages tenant configuration and integrations | Multi-tenancy isolation, API health, configuration versioning, deployment pipelines |
| Finance / Billing Manager | Oversees premium collection and reconciliation | Installment accuracy, NSF handling, aging reports, payment gateway reconciliation |
| Executive / C-Suite | Monitors business performance | Combined ratio dashboards, written premium trends, claims severity, renewal retention rates |

---

## Functional Requirements

### Policy Management

**FR-POL-001 — Policy Application Intake**
The system shall accept policy applications via broker portal submission, API integration, or direct data entry. Applications must capture insured demographics, coverage selections, property or vehicle schedules, prior loss history, and jurisdictional eligibility fields.

**FR-POL-002 — Multi-Step Quote Generation**
The system shall generate bindable quotes within 30 seconds for straight-through processing (STP) eligible risks, applying configured rate tables, surcharges, credits, and minimum premium rules per line of business and state.

**FR-POL-003 — Policy Binding and Issuance**
Upon binding, the system shall assign a unique policy number, generate a declarations page, issue all required statutory notices, and record the effective date, expiration date, and coverage schedule in the policy record.

**FR-POL-004 — Policy Endorsement Processing**
The system shall support mid-term endorsements including coverage changes, insured substitutions, vehicle or property schedule changes, and name-insured updates. Each endorsement shall generate a revised declarations page and a pro-rata or short-rate premium adjustment.

**FR-POL-005 — Policy Renewal Workflow**
The system shall automatically generate renewal notices 90, 60, and 30 days before expiration. Renewal offers must re-rate at current filed rates and flag policies whose risk profile has changed materially since inception.

**FR-POL-006 — Policy Cancellation and Non-Renewal**
The system shall support flat, pro-rata, and short-rate cancellations initiated by insured, broker, or carrier. Cancellation notices must comply with state-mandated advance notice periods (minimum 10–60 days by state). Non-renewal notices must be generated per jurisdiction rules.

**FR-POL-007 — Policy Reinstatement**
The system shall support reinstatement of cancelled policies within carrier-configured windows, subject to lapse rules and back-premium collection. Reinstatements must regenerate a lapse-free or lapsed policy history flag for underwriting review.

**FR-POL-008 — Document Generation and Delivery**
The system shall produce all policy documents — declarations pages, certificates of insurance, endorsements, cancellation notices, and ID cards — as versioned PDFs. Documents shall be deliverable via email, policyholder portal download, or postal mail fulfillment API.

**FR-POL-009 — Policy Search and Retrieval**
The system shall provide full-text and field-level search across all policies by policy number, insured name, tax ID, vehicle VIN, property address, and broker of record. Search results must return within 2 seconds for datasets up to 10 million policies.

**FR-POL-010 — Policy Version History and Audit Trail**
Every change to a policy record — rate, coverage, endorsement, status transition — shall create an immutable version snapshot with timestamp, user identity, and reason code. The full transaction history must be accessible in the UI and exportable as a structured report.

---

### Underwriting

**FR-UND-001 — Configurable Underwriting Rules Engine**
The platform shall provide a no-code rules engine enabling underwriters to define acceptance criteria, declination rules, referral triggers, and rate modification factors per line of business, state, and risk category without software deployments.

**FR-UND-002 — Automated Risk Scoring**
For eligible lines, the system shall compute a composite risk score using internal loss history, external credit score, ISO CLUE report data, property characteristics, and territory factors. Score bands must map to automatic approval, referral, or declination outcomes.

**FR-UND-003 — Referral Queue Management**
Submissions that do not qualify for straight-through processing shall enter a prioritized referral queue. Underwriters shall be able to view, assign, annotate, approve, modify, or decline referrals with full supporting data visible in a single screen.

**FR-UND-004 — External Data Integration for Underwriting**
The system shall integrate with LexisNexis CLUE, ISO/Verisk property reports, state MVR services, and commercial credit bureaus. External data pulls must be logged, cached per configurable TTL, and auditable.

**FR-UND-005 — Underwriting Appetite Configuration**
Carriers shall be able to configure product appetite by territory, construction type, occupancy class, prior loss count, and credit tier. Appetite changes must be version-controlled with effective dates and impact analysis before activation.

**FR-UND-006 — Reinsurance Threshold Flagging**
During underwriting, the system shall identify risks that exceed facultative reinsurance thresholds and automatically generate a reinsurance placement referral with the risk schedule attached.

**FR-UND-007 — Underwriting Override Workflow**
Senior underwriters shall be able to override automatic declinations with documented justification. All overrides must be captured in the audit trail with approver identity, override reason, and any attached supporting documents.

**FR-UND-008 — Underwriting Analytics Dashboard**
The system shall provide real-time dashboards showing hit ratio, STP rate, referral aging, declination reasons by category, and written premium by underwriter, territory, and line of business.

---

### Claims Processing

**FR-CLM-001 — FNOL Intake**
The system shall accept First Notice of Loss via policyholder portal, broker portal, inbound API, or phone-assisted manual entry. FNOL must capture date of loss, loss type, location, description, contact information, and any available police or incident report references.

**FR-CLM-002 — Coverage Verification**
Upon FNOL submission, the system shall automatically verify policy coverage in force at the date of loss, applicable deductibles, coverage limits, and any exclusions. Coverage verification results must be surfaced to the adjuster within the claim record.

**FR-CLM-003 — Claim Assignment and Routing**
Claims shall be automatically assigned to adjusters based on configurable routing rules: line of business, loss type, estimated severity band, geographic territory, and workload balancing. Manual reassignment must be supported with reason logging.

**FR-CLM-004 — Reserves Management**
Adjusters shall be able to set, update, and close indemnity, expense, and subrogation reserves per coverage part. Reserve changes exceeding configurable authority thresholds must follow an approval workflow. The system shall track case reserves, incurred-but-not-reported (IBNR) imports, and reserve adequacy ratios.

**FR-CLM-005 — Claims Investigation Workflow**
The system shall support structured investigation tasks: inspection scheduling, recorded statement tracking, independent medical examination (IME) referrals, salvage and subrogation identification, and vendor assignment for appraisals and expert witnesses.

**FR-CLM-006 — Document and Evidence Management**
Each claim shall have a document repository supporting upload of photos, videos, police reports, medical records, repair estimates, and correspondence. Documents must be versioned, virus-scanned, and accessible with role-based permissions.

**FR-CLM-007 — Payment and Settlement Processing**
The system shall support claims payments via check issuance, ACH, and virtual card. Payments must include payee validation, duplicate payment checks, lien holder notifications, and mortgage payee endorsement for property claims. Settlement agreements shall require digital signature capture.

**FR-CLM-008 — Subrogation and Salvage Tracking**
The system shall identify subrogation opportunities at FNOL and track recovery efforts through demand letter, negotiation, arbitration (Arbitration Forums integration), and collection. Salvage titles and recovery receipts shall reduce net claim cost automatically.

**FR-CLM-009 — Fraud Indicator Flagging**
The system shall apply configurable fraud indicator rules — pattern matching, anomaly scoring, and SIU referral triggers — at FNOL and throughout the claims lifecycle. Flagged claims must enter an SIU review queue with supporting indicators documented.

**FR-CLM-010 — Claims Reporting and Analytics**
The system shall provide loss run reports, claims aging reports, adjuster productivity reports, large-loss alerts, and closed-without-payment analysis. Loss runs must be exportable in ISO LOSS/ALF format and available to brokers for renewal submissions.

---

### Premium Billing

**FR-BIL-001 — Installment Plan Configuration**
The system shall support configurable installment plans: annual, semi-annual, quarterly, monthly, and custom schedules. Plans must support minimum down payments, service fee structures, and grace period windows per state regulatory requirements.

**FR-BIL-002 — Invoice and Statement Generation**
The system shall generate itemized billing statements showing premium breakdown by coverage part, taxes, surcharges, fees, and installment amounts. Statements must be delivered on configurable schedules via email, portal, or mail.

**FR-BIL-003 — Payment Processing**
The system shall integrate with payment gateways to accept credit card (Visa, Mastercard, Amex), ACH/eCheck, and digital wallet payments. Tokenized payment methods must be stored for recurring billing. PCI-DSS compliance is mandatory.

**FR-BIL-004 — NSF and Failed Payment Handling**
The system shall automatically retry failed ACH payments per configurable retry schedules, assess NSF fees where permitted by state law, issue notice of cancellation for non-payment per jurisdiction rules, and suspend coverage at the statutory lapse date.

**FR-BIL-005 — Premium Reconciliation**
The system shall reconcile collected premium against policy-level earned premium daily. Variances must be flagged for billing team review. Reconciliation reports must be exportable for general ledger journal entry import.

**FR-BIL-006 — Broker Commission Management**
The system shall calculate broker commissions based on configurable commission schedules (flat rate, sliding scale, contingent) and generate commission statements per billing cycle. Chargebacks for mid-term cancellations must be calculated and tracked.

**FR-BIL-007 — Premium Financing Integration**
The system shall support integration with premium finance companies. Financed policies must track premium finance agreement (PFA) reference, financing company, and enable power-of-attorney cancellation notices to be issued upon default notification from the finance company.

**FR-BIL-008 — Billing Regulatory Compliance**
All billing notices — first notice, reminder, notice of cancellation, notice of non-renewal — must comply with state-mandated timing, content, and delivery format requirements, configurable per jurisdiction.

---

### Reinsurance

**FR-REI-001 — Treaty and Facultative Agreement Configuration**
The system shall allow configuration of proportional (quota share, surplus share) and non-proportional (excess of loss, catastrophe XL) treaty structures, including attachment points, limits, co-participation percentages, and reinsurer panel participation shares.

**FR-REI-002 — Automatic Cession Calculation**
For each bound policy, the system shall calculate cessions under applicable treaties, allocate net and ceded premium, and record gross, ceded, and net amounts at the coverage and policy level.

**FR-REI-003 — Bordereaux Generation**
The system shall generate monthly and quarterly premium and loss bordereau reports formatted per reinsurer specifications. Bordereaux must include policy schedule, ceded premium, ceded losses, and reserves by treaty and coverage layer.

**FR-REI-004 — Facultative Placement Workflow**
For risks requiring facultative placement, the system shall generate a risk schedule, track reinsurer offers and lines, record final placement, and update the policy record with confirmed facultative coverage.

**FR-REI-005 — Reinsurance Recoverable Tracking**
The system shall track outstanding reinsurance recoverables by treaty, claim, and reinsurer. Aging of recoverables must be reported and cash calls generated when collection thresholds are exceeded.

**FR-REI-006 — Catastrophe Accumulation Monitoring**
The system shall aggregate exposures by geographic zone, peril, and treaty layer to enable real-time catastrophe accumulation monitoring against treaty limits and regulatory surplus requirements.

---

### Broker Portal

**FR-BRK-001 — Broker Registration and Credentialing**
The system shall maintain a broker/agent registry with license verification, appointment status per state, binding authority limits by line of business, and E&O insurance expiration tracking.

**FR-BRK-002 — Online Submission and Quoting**
Brokers shall be able to submit new business applications, retrieve bindable quotes, compare coverage options, and bind eligible risks within their authority limits without underwriter involvement for STP risks.

**FR-BRK-003 — Broker Dashboard and Book of Business**
Brokers shall have access to a dashboard showing their active policies, expiring policies (30/60/90 days), open claims, outstanding premium balances, commission statements, and new business performance metrics.

**FR-BRK-004 — Certificate of Insurance Issuance**
Brokers shall be able to generate and issue ACORD-compliant Certificates of Insurance (COI) for eligible policies without carrier intervention, subject to coverage restrictions defined by the carrier in the platform.

**FR-BRK-005 — Broker Communication and Notifications**
The system shall send brokers automated notifications for: policy expiration, mid-term cancellation, claim status updates, payment delinquency, and underwriting referral decisions. Notification preferences must be configurable by broker.

**FR-BRK-006 — Wholesale and Retail Broker Hierarchy**
The system shall support multi-level broker hierarchies — retail, wholesale, and MGA — with configurable commission splits, sub-producer tracking, and delegated underwriting authority at each tier.

---

### Regulatory Reporting

**FR-REG-001 — NAIC Annual Statement Preparation**
The system shall produce data extracts and exhibit schedules required for the NAIC Property/Casualty Annual Statement (blank), including Schedules D, F, P, and the underwriting and investment exhibits, in XBRL/iXBRL format.

**FR-REG-002 — State Filing Management via SERFF**
The system shall integrate with SERFF (System for Electronic Rate and Form Filing) to submit rate, rule, and form filings. Filing status must be tracked within the platform and approvals must trigger automatic product configuration updates.

**FR-REG-003 — Statistical Reporting**
The system shall produce ISO statistical reporting unit (SRU) data and NCCI workers' compensation statistical reports per state data call requirements. Reports must be validated against bureau edit specifications before submission.

**FR-REG-004 — Surplus Lines Compliance**
For non-admitted business, the system shall track surplus lines eligibility, generate surplus lines tax calculations by state, produce diligent search documentation, and support surplus lines stamp filing workflows.

**FR-REG-005 — Market Conduct Audit Support**
The system shall support market conduct examination requests by enabling production of complete policy files, claim files, billing histories, and underwriting decision logs within a defined date range, exportable in examiner-specified formats.

**FR-REG-006 — Regulatory Calendar and Alerts**
The system shall maintain a regulatory calendar with configurable alerts for filing deadlines, license renewal dates, admitted product form approval expirations, and NAIC blanks submission deadlines.

---

## Non-Functional Requirements

### Performance

- Policy quote generation for STP risks: ≤ 30 seconds end-to-end including external data pulls
- Policy search results: ≤ 2 seconds for up to 10 million policy records
- Claims FNOL submission: ≤ 5 seconds to acknowledgment
- Batch renewals: process 50,000 policies per hour during off-peak renewal cycles
- Bordereaux generation: complete within 4 hours for monthly close across all treaties
- API response time (p99): ≤ 500 ms for read operations, ≤ 2 seconds for write operations

### Availability

- System availability: 99.9% uptime SLA (≤ 8.7 hours unplanned downtime per year)
- Planned maintenance windows: permitted during Sunday 02:00–06:00 local carrier time
- Recovery Time Objective (RTO): ≤ 4 hours for full platform restore
- Recovery Point Objective (RPO): ≤ 15 minutes (continuous replication to standby region)
- Disaster recovery failover: automated, tested semi-annually

### Security

- Authentication: SAML 2.0 and OIDC federation for enterprise SSO; MFA required for all privileged roles
- Authorization: attribute-based access control (ABAC) with policy-level data isolation between tenants
- Data encryption: AES-256 at rest; TLS 1.3 in transit; field-level encryption for PII and payment data
- Vulnerability management: SAST/DAST scans on every release; penetration testing annually
- Session management: configurable idle timeout (default 15 minutes for claims and underwriting roles)
- Audit logging: tamper-evident logs for all data access, modifications, and administrative actions retained for 7 years

### Compliance

- SOC 2 Type II certification covering Security, Availability, and Confidentiality trust service criteria
- PCI-DSS Level 1 Service Provider compliance for all payment card data handling
- NAIC Insurance Data Security Model Law compliance (NAIC MDL-668)
- CCPA compliance for California policyholders: consent management, data subject rights, and data inventory

### Scalability

- Multi-tenant SaaS architecture supporting up to 100 carrier tenants concurrently
- Horizontal auto-scaling for API and processing tiers triggered at 70% CPU or memory utilization
- Database: sharded by tenant with cross-shard query support for regulatory reporting aggregation
- Storage: object storage for documents with lifecycle tiering to cold storage after 90 days of inactivity

---

## Regulatory Compliance Requirements

- **NAIC MDL-668 (Insurance Data Security Model Law):** Information Security Program, incident response plan, annual board reporting, and third-party vendor security assessments
- **NAIC MDL-672 (Privacy of Consumer Financial and Health Information):** Privacy notices, opt-out mechanisms, and restrictions on sharing nonpublic personal information
- **State Rate and Form Filing Laws:** All rates, rules, and policy forms must be filed and approved (prior approval states) or filed and effective (file-and-use states) before use in each jurisdiction
- **State Cancellation and Non-Renewal Statutes:** Statutory advance notice periods, permitted cancellation reasons, and required notice content enforced per jurisdiction
- **Workers' Compensation Exclusive Remedy:** WC line must enforce state fund exclusivity rules and NCCI classification adherence where applicable
- **Surplus Lines Regulations:** Diligent search requirements, surplus lines tax rates, stamping office submission, and Quarterly/Annual filing obligations per NIMA and state regulations
- **OFAC Compliance:** Automated OFAC SDN screening on all new policies, endorsements, and claim payments; blocked transactions must trigger compliance review workflow

---

## Integration Requirements

| Integration | Protocol | Purpose |
|---|---|---|
| ISO/Verisk CLUE | REST API | Prior loss history for underwriting |
| LexisNexis Attract | REST API | Credit-based insurance score |
| State MVR Services | State-specific REST/SFTP | Motor vehicle records for auto underwriting |
| ISO xactimate / CoreLogic | REST API | Property valuation and replacement cost estimation |
| SERFF | SFTP + Web Services | Rate and form filing submission and status tracking |
| ISO Statistical Reporting | SFTP (fixed-width) | Bureau statistical reporting unit data submission |
| Stripe / Braintree | REST API | Payment card processing and tokenization |
| Dwolla / Plaid | REST API | ACH payment initiation and bank account verification |
| DocuSign | REST API | Digital signature for settlement agreements and PFAs |
| SendGrid / Twilio | REST API | Transactional email and SMS notification delivery |
| Guidewire BillingCenter | REST API | Optional billing engine integration for migrating carriers |
| Reinsurance platforms (Sequel, Rein4ce) | SFTP + REST | Bordereaux and cession data exchange |
| NAIC iSite+ | SFTP + XBRL | Annual statement filing submission |

---

## Constraints and Assumptions

### Constraints

- The platform must operate exclusively within U.S. jurisdiction in v1.0; international expansion is deferred
- All filed rate tables must be stored in immutable versioned records; retroactive rate changes are prohibited
- Payment card data must never be stored in the application database; tokenization via payment gateway is mandatory
- Regulatory filing integrations are dependent on SERFF API availability; fallback to manual upload must be supported
- Multi-tenancy requires complete data isolation; cross-tenant data access is a critical security boundary

### Assumptions

- Carrier tenants will provide their own actuarially justified rate filings and loss development factors; the platform does not perform actuarial analysis
- External data vendors (LexisNexis, ISO) will provide sandbox environments for integration testing in lower environments
- Broker licensing verification is performed via NIPR API; the platform assumes NIPR data is current within a 24-hour cache window
- State regulatory content (cancellation periods, filing requirements) will be maintained by the platform operator as a managed content library
- Policyholders are assumed to have provided affirmative consent to electronic delivery of policy documents as a condition of account creation
- The platform assumes existing carrier core systems (if any) will provide policy history data migration via bulk import tooling; real-time legacy system integration is out of scope for v1.0
