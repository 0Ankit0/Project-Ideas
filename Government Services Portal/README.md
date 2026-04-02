# Government Services Portal

> A unified citizen-facing digital government services platform — apply for permits, licenses, certificates, pay fees, and interact with departments entirely online.

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Key Features](#key-features)
3. [Primary Roles](#primary-roles)
4. [Getting Started](#getting-started)
5. [Documentation Status](#documentation-status)
6. [Delivery Blueprint](#delivery-blueprint)
7. [Operational Policy Addendum](#operational-policy-addendum)

---

## Directory Structure

```
Government Services Portal/
├── README.md
├── requirements/
│   ├── requirements-document.md
│   └── user-stories.md
├── analysis/
│   ├── domain-model.md
│   ├── data-flow-diagrams.md
│   ├── risk-register.md
│   └── stakeholder-map.md
├── high-level-design/
│   ├── system-architecture.md
│   ├── api-design.md
│   ├── database-schema.md
│   ├── auth-flows.md
│   └── integration-map.md
├── detailed-design/
│   ├── citizen-identity-module.md
│   ├── service-catalog-module.md
│   ├── workflow-engine.md
│   ├── permit-license-module.md
│   ├── payment-module.md
│   ├── document-vault-module.md
│   ├── status-tracking-module.md
│   ├── department-admin-module.md
│   ├── grievance-module.md
│   └── accessibility-multilingual.md
├── infrastructure/
│   ├── aws-architecture.md
│   ├── deployment-guide.md
│   ├── monitoring-alerting.md
│   ├── disaster-recovery.md
│   └── security-hardening.md
├── implementation/
│   ├── coding-standards.md
│   ├── testing-strategy.md
│   ├── ci-cd-pipeline.md
│   └── performance-testing.md
└── edge-cases/
    ├── auth-edge-cases.md
    ├── payment-edge-cases.md
    ├── workflow-edge-cases.md
    └── document-edge-cases.md
```

---

## Key Features

- **Unified Service Catalog**: Citizens can browse, search, and filter all available government services across departments — permits, licenses, certificates, welfare schemes — from a single portal. Services are tagged by category, department, eligibility criteria, and estimated processing time.

- **Nepal Document Wallet (NDW) / NID OTP Authentication**: Secure citizen identity verification using Nepal Document Wallet (NDW) OAuth 2.0 and NID-based OTP issued through the NASC (National Identity Management Centre) authentication gateway. Citizens can also sign in via email OTP or SMS OTP. Optional biometric authentication is supported for kiosk deployments.

- **Visual Application Workflow Tracker**: Every submitted application moves through a configurable state machine (Draft → Submitted → Under Review → Field Verification → Approved / Rejected / Returned for Correction). Citizens receive real-time status updates via SMS, email, and in-portal notifications at every transition.

- **Dynamic Multi-Step Application Forms**: Service forms are schema-driven and rendered dynamically by the frontend. Forms support conditional logic (show/hide fields based on prior answers), file uploads, address auto-fill from NID, and multi-language display with full RTL support.

- **Integrated Fee Payment**: Citizens can pay service fees using ConnectIPS (official Government of Nepal payment gateway), Razorpay Government integration, eSewa/Khalti/ConnectIPS, net banking, debit/credit cards, or offline challan generation. Automated payment reconciliation runs nightly via Celery tasks.

- **Encrypted Document Vault**: Citizens upload supporting documents (NID, PAN, income certificate, photographs) once and reuse them across multiple applications. Documents are stored encrypted at rest in AWS S3 with AWS KMS, and all signed certificates issued by departments use DSC (Digital Signature Certificate) signing.

- **Permit & License Lifecycle Management**: Issued permits and licenses have a full lifecycle tracked by the system — issuance, validity period, renewal reminders (60-day, 30-day, 7-day prior), suspension, revocation, and re-issuance after correction. QR code–based digital permit verification is supported.

- **Grievance Redressal System**: Citizens can file grievances against delayed or rejected applications. Grievances are auto-assigned to the responsible department, escalated on SLA breach (3-day → 7-day → Commissioner-level escalation), and resolved with a mandatory written response. An appeal mechanism allows re-escalation to an ombudsman.

- **Multilingual Support (12 Languages)**: The portal supports English, Hindi, Bengali, Telugu, Tamil, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi, and Urdu. All UI strings are loaded from language bundles stored in PostgreSQL and served via CDN. SMS notifications are sent in the citizen's preferred language.

- **WCAG 2.1 AA Accessibility**: The frontend is built to WCAG 2.1 Level AA standards — full keyboard navigation, screen reader compatibility (NVDA, JAWS, VoiceOver), minimum 4.5:1 contrast ratio, focus indicators, ARIA labels on all interactive elements, and skip-navigation links. Automated axe-core accessibility scans run on every CI build.

- **SMS Fallback for Low-Connectivity Zones**: Citizens without smartphone access can interact with the portal over SMS using structured keyword commands (e.g., `STATUS <application-id>`, `PAY <challan-id>`, `TRACK <permit-id>`). An Nepal Telecom / Sparrow SMS gateway adapter translates inbound messages into portal API calls and returns formatted SMS responses.

- **Department Admin Console**: Department Heads and Field Officers have a dedicated console to manage incoming applications — view queues, assign officers, request additional documents, approve/reject/return applications, generate reports, and manage department-level service configurations.

- **Audit Trail & Compliance Reporting**: Every system action (login, form save, document upload, payment, status change, admin override) is written to an immutable audit log stored in a separate append-only PostgreSQL schema. The Auditor role can export audit reports filtered by date, user, department, service, or action type.

- **Infrastructure-Grade Security**: The platform runs behind AWS WAF with managed rule groups for OWASP Top 10 and government-specific threat patterns. AWS Shield Standard provides DDoS protection. All API endpoints are rate-limited, all PII fields are encrypted at the column level using Django's field-level encryption library, and all inter-service communication uses mutual TLS.

- **Automated Celery Workflow Tasks**: Background Celery workers handle: payment reconciliation, document virus scanning (ClamAV integration), permit renewal reminders, SLA breach escalations, offline challan expiry, bulk SMS dispatch, and nightly analytics aggregation. Workers are deployed as separate ECS Fargate task definitions with auto-scaling.

- **Configurable SLA Engine**: Each service in the catalog has a configurable SLA (number of working days for approval, reminder intervals, escalation levels). The workflow engine evaluates SLA compliance on every status transition and raises automated escalation events when deadlines are missed.

- **Role-Based Access Control (RBAC)**: Five distinct roles with fine-grained permission sets are enforced at the Django API layer and replicated in the Next.js frontend for UI gating. Permissions are checked on every API request through Django REST Framework's permission classes and JWT claims.

---

## Primary Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **Citizen** | Registered individual accessing the portal to apply for government services, make payments, track applications, and file grievances. | Register & authenticate via NID/Nepal Document Wallet (NDW); browse service catalog; submit applications; upload documents to personal vault; make fee payments; track application status; file and track grievances; download issued certificates and permits. |
| **Field Officer** | A department staff member responsible for reviewing submitted applications, conducting field verifications, requesting additional documents, and making approval recommendations. | View assigned application queue; update application status (Under Review, Field Verification, Return for Correction, Recommend Approval/Reject); attach field inspection notes and photos; communicate with citizens via in-portal messaging; cannot make final approval decisions. |
| **Department Head** | Senior department official with authority to make final approval or rejection decisions, configure service parameters, view department-level analytics, and manage officer assignments. | All Field Officer permissions; final approve/reject applications; reassign applications between officers; configure SLAs and fee schedules for department services; view department dashboards and reports; issue bulk approvals for routine applications. |
| **Super Admin** | Platform-level administrator responsible for managing departments, users, service catalog, system configuration, and cross-department coordination. | Full system access; create/deactivate departments and users; manage the global service catalog; configure payment gateway parameters; access all audit logs; manage multilingual content; trigger manual Celery tasks; configure WAF rules and system alerts. |
| **Auditor** | An independent or internal auditor with read-only access to audit trails, transaction logs, and compliance reports for regulatory and internal audit purposes. | Read-only access to full audit log; export audit reports by date range, user, department, service, or event type; view all payment transaction records; view citizen identity verification logs; cannot modify any data. |

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/government-services-portal.git
   cd government-services-portal
   ```

2. **Create and activate a Python virtual environment**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

4. **Install Node.js dependencies for the frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Configure environment variables**
   Copy the example environment file and populate all required values:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.local.example frontend/.env.local
   ```
   Key variables to set in `backend/.env`:
   - `DATABASE_URL` — PostgreSQL 15 connection string
   - `REDIS_URL` — Redis 7 connection string
   - `SECRET_KEY` — Django secret key (generate with `python -c "import secrets; print(secrets.token_hex(50))"`)
   - `AADHAAR_CLIENT_ID`, `AADHAAR_CLIENT_SECRET` — NASC (National Identity Management Centre) sandbox credentials
   - `DIGILOCKER_CLIENT_ID`, `DIGILOCKER_CLIENT_SECRET` — Nepal Document Wallet (NDW) OAuth credentials
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, `AWS_KMS_KEY_ID`
   - `PAYGOV_MERCHANT_ID`, `PAYGOV_SECRET_KEY` — ConnectIPS sandbox credentials
   - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` — Razorpay Government sandbox credentials
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SMS_FROM` — Nepal Telecom / Sparrow SMS gateway credentials
   - `CELERY_BROKER_URL` — typically the same as `REDIS_URL`

6. **Start PostgreSQL and Redis locally** (if not using managed services)
   ```bash
   docker compose -f docker-compose.dev.yml up -d postgres redis
   ```

7. **Run database migrations**
   ```bash
   cd backend
   python manage.py migrate
   ```

8. **Load seed fixtures** (departments, service catalog, role permissions, multilingual strings)
   ```bash
   python manage.py loaddata fixtures/departments.json
   python manage.py loaddata fixtures/services.json
   python manage.py loaddata fixtures/permissions.json
   python manage.py loaddata fixtures/languages.json
   python manage.py loaddata fixtures/sla_configs.json
   ```

9. **Create a Super Admin account**
   ```bash
   python manage.py createsuperuser
   ```

10. **Start the Celery worker and beat scheduler**
    ```bash
    celery -A govportal worker --loglevel=info --concurrency=4 &
    celery -A govportal beat --loglevel=info &
    ```

11. **Start the Django development server**
    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

12. **Start the Next.js frontend development server**
    ```bash
    cd frontend
    npm run dev
    ```

13. **Access the portal**
    - Citizen Portal: [http://localhost:3000](http://localhost:3000)
    - Department Admin Console: [http://localhost:3000/admin](http://localhost:3000/admin)
    - Django API Root: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
    - Django Admin (Super Admin): [http://localhost:8000/django-admin/](http://localhost:8000/django-admin/)

---

## Documentation Status

| # | File | Status |
|---|------|--------|
| 1 | `README.md` | ✅ Complete |
| 2 | `requirements/requirements-document.md` | ✅ Complete |
| 3 | `requirements/user-stories.md` | ✅ Complete |
| 4 | `analysis/domain-model.md` | ✅ Complete |
| 5 | `analysis/data-flow-diagrams.md` | ✅ Complete |
| 6 | `analysis/risk-register.md` | ✅ Complete |
| 7 | `analysis/stakeholder-map.md` | ✅ Complete |
| 8 | `high-level-design/system-architecture.md` | ✅ Complete |
| 9 | `high-level-design/api-design.md` | ✅ Complete |
| 10 | `high-level-design/database-schema.md` | ✅ Complete |
| 11 | `high-level-design/auth-flows.md` | ✅ Complete |
| 12 | `high-level-design/integration-map.md` | ✅ Complete |
| 13 | `detailed-design/citizen-identity-module.md` | ✅ Complete |
| 14 | `detailed-design/service-catalog-module.md` | ✅ Complete |
| 15 | `detailed-design/workflow-engine.md` | ✅ Complete |
| 16 | `detailed-design/permit-license-module.md` | ✅ Complete |
| 17 | `detailed-design/payment-module.md` | ✅ Complete |
| 18 | `detailed-design/document-vault-module.md` | ✅ Complete |
| 19 | `detailed-design/status-tracking-module.md` | ✅ Complete |
| 20 | `detailed-design/department-admin-module.md` | ✅ Complete |
| 21 | `detailed-design/grievance-module.md` | ✅ Complete |
| 22 | `detailed-design/accessibility-multilingual.md` | ✅ Complete |
| 23 | `infrastructure/aws-architecture.md` | ✅ Complete |
| 24 | `infrastructure/deployment-guide.md` | ✅ Complete |
| 25 | `infrastructure/monitoring-alerting.md` | ✅ Complete |
| 26 | `infrastructure/disaster-recovery.md` | ✅ Complete |
| 27 | `infrastructure/security-hardening.md` | ✅ Complete |
| 28 | `implementation/coding-standards.md` | ✅ Complete |
| 29 | `implementation/testing-strategy.md` | ✅ Complete |
| 30 | `implementation/ci-cd-pipeline.md` | ✅ Complete |
| 31 | `implementation/performance-testing.md` | ✅ Complete |
| 32 | `edge-cases/auth-edge-cases.md` | ✅ Complete |
| 33 | `edge-cases/payment-edge-cases.md` | ✅ Complete |
| 34 | `edge-cases/workflow-edge-cases.md` | ✅ Complete |
| 35 | `edge-cases/document-edge-cases.md` | ✅ Complete |

---

## Delivery Blueprint

| Phase | Deliverable | Owner | Status | Sprint |
|-------|-------------|-------|--------|--------|
| **Phase 1 — Discovery** | Stakeholder interviews, As-Is process mapping, pain-point analysis, preliminary scope definition, signed Project Charter | Business Analyst + Project Manager | ✅ Complete | Sprint 0 |
| **Phase 1 — Discovery** | Regulatory compliance checklist (IT Act 2000, NID Act, PDPA, GFR 2017), Legal review of data handling obligations | Legal + Compliance Team | ✅ Complete | Sprint 0 |
| **Phase 2 — Analysis** | Domain model, stakeholder map, data-flow diagrams (DFD Level 0, 1, 2), risk register with mitigation plans | Business Analyst + Solutions Architect | ✅ Complete | Sprint 1 |
| **Phase 2 — Analysis** | Software Requirements Specification (SRS), User Stories with acceptance criteria, non-functional requirements baseline | Business Analyst | ✅ Complete | Sprint 1–2 |
| **Phase 3 — High-Level Design** | System architecture diagram (AWS ECS Fargate topology), technology selection rationale, integration map with NASC (National Identity Management Centre)/Nepal Document Wallet (NDW)/ConnectIPS/NIC | Solutions Architect | ✅ Complete | Sprint 2–3 |
| **Phase 3 — High-Level Design** | REST API contract (OpenAPI 3.1 spec), Authentication flow diagrams, Database schema (ER diagram + DDL), High-level security design | Solutions Architect + Lead Engineer | ✅ Complete | Sprint 3 |
| **Phase 4 — Detailed Design** | Module-level detailed design for all 10 core domains (Citizen Identity, Service Catalog, Workflow Engine, Permits, Payments, Document Vault, Status Tracking, Admin Console, Grievance, Accessibility) | Lead Engineers (Backend + Frontend) | ✅ Complete | Sprint 4–6 |
| **Phase 4 — Detailed Design** | Edge case analysis for Auth, Payment, Workflow, and Documents; sequence diagrams for all critical flows; error handling matrix | Lead Engineers | ✅ Complete | Sprint 5–6 |
| **Phase 5 — Infrastructure** | AWS architecture design (ECS Fargate, RDS Multi-AZ, ElastiCache, CloudFront, Route 53, WAF, Shield), IaC (Terraform), disaster recovery plan, monitoring & alerting design (CloudWatch, PagerDuty) | DevOps / Cloud Engineer | ✅ Complete | Sprint 6–7 |
| **Phase 5 — Infrastructure** | Security hardening guide, CI/CD pipeline design (GitHub Actions → ECR → ECS), deployment runbook, performance testing plan | DevOps + QA Engineers | ✅ Complete | Sprint 7 |
| **Phase 6 — Implementation** | Coding standards guide, testing strategy (unit/integration/E2E/load), CI/CD pipeline implementation, production deployment | Development Team | 🔄 In Progress | Sprint 8–18 |
| **Phase 6 — Implementation** | UAT with selected pilot departments, accessibility audit, penetration testing, go-live checklist, hypercare support | QA + Security + Project Team | 🔜 Planned | Sprint 17–20 |

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policies

**CDP-001 — NID Data Minimisation**
The portal shall collect only the NID number and associated OTP token for identity verification purposes. The full NID number shall never be stored in the portal database; only a masked reference (last 4 digits) and the NASC (National Identity Management Centre) authentication token shall be persisted. This complies with Section 29 of the NID (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016, which prohibits storage of NID numbers by requesting entities beyond the scope required for authentication.

**CDP-002 — Personal Data Protection Act (PDPA) Compliance**
All citizen personal data (name, address, date of birth, phone number, email, income data, family details) collected through the portal is classified as Personal Data under the Digital Personal Data Protection Act, 2023. Citizens must provide explicit consent before submitting an application. Consent records are stored with a timestamp, IP address, and the specific consent text shown at the time. Citizens can withdraw consent and request erasure of personal data through the Account Settings screen, subject to statutory retention requirements.

**CDP-003 — IT Act 2000 / Information Technology (Reasonable Security Practices) Rules 2011**
The portal implements reasonable security practices as mandated by the IT Act 2000 and the associated Rules. This includes: AES-256 encryption of Sensitive Personal Data (SPD) in the database, TLS 1.3 for all data in transit, regular security audits, and a documented information security policy accessible to all staff. Any data breach involving SPD is reported to CERT-In within 6 hours of discovery as required by the CERT-In Directions (April 2022).

**CDP-004 — Citizen Data Access Rights**
Citizens have the right to access, correct, and download their personal data held by the portal. The Account Settings section provides a "Download My Data" feature that generates a machine-readable JSON export of all citizen profile data, application submissions, payment history, and documents within 24 hours of request. Data correction requests are processed within 3 working days by the relevant department.

**CDP-005 — Third-Party Data Sharing Restrictions**
Citizen personal data shall not be shared with any third party outside the government ecosystem without explicit citizen consent, except where required by law (e.g., court orders, law enforcement requests under Section 69 of the IT Act 2000). Payment gateway integrations (ConnectIPS, Razorpay Government) receive only the transaction amount, purpose code, and a non-PII reference ID — no NID, PAN, or address data is transmitted. Nepal Document Wallet (NDW) and NASC (National Identity Management Centre) integrations operate on the principle of federated identity: personal documents are fetched on-demand and never cached beyond the active session.

**CDP-006 — Data Retention Schedule**
Citizen application records are retained for 7 years after the application's final resolution (approval/rejection/withdrawal) to comply with GFR (General Financial Rules) 2017 and departmental archiving mandates. Audit logs are retained for 10 years. After the retention period, data is securely deleted using NIST SP 800-88 compliant media sanitization procedures. Citizens are notified 90 days before scheduled deletion of their personal data.

---

### 2. Service Delivery SLA Policies

**SLA-001 — Portal Availability Target**
The production portal must achieve a minimum availability of 99.9% measured on a rolling monthly basis, excluding scheduled maintenance windows. This corresponds to a maximum allowable downtime of 43.8 minutes per month. AWS ECS Fargate multi-AZ deployment with auto-scaling and an Application Load Balancer ensures high availability. Availability is continuously monitored via CloudWatch Synthetic Canaries pinging all critical citizen-facing endpoints every 60 seconds.

**SLA-002 — API Response Time SLA**
All citizen-facing API endpoints must respond within 500 ms for the 95th percentile (p95) of requests under normal load (up to 5,000 concurrent users). Document upload endpoints are exempt and must respond within 3,000 ms for the 95th percentile. Database query time must not exceed 100 ms for 99% of queries. CloudFront caching is used for all static assets and public service catalog data to reduce origin load. Redis caching is used for session data, OTP tokens, and frequently accessed application status queries.

**SLA-003 — Application Processing Time SLAs (per service type)**
Each service in the catalog is configured with a departmental SLA defining the maximum number of working days for processing:
- Routine certificates (birth/death/caste/income/domicile): 3 working days
- Trade licenses and renewals: 7 working days
- Building permits (residential): 15 working days
- Building permits (commercial/industrial): 30 working days
- Environmental clearances: 45 working days
- Welfare scheme enrollment: 10 working days
The workflow engine monitors these SLAs and sends automated escalation notifications to the Department Head when 75% of the SLA period has elapsed without resolution.

**SLA-004 — Grievance Resolution SLA**
Filed grievances must receive an initial acknowledgement within 24 hours and a substantive response within 3 working days. If unresolved after 3 working days, the grievance is automatically escalated to the Department Head. If unresolved after 7 working days, it is escalated to the Commissioner level. If unresolved after 15 working days, it is escalated to a designated ombudsman officer. All escalations are logged in the audit trail and trigger email/SMS notifications to the citizen.

**SLA-005 — Payment Processing SLA**
Online payments (ConnectIPS/Razorpay) must be confirmed and reflected in the application status within 5 minutes of successful payment. Payment reconciliation with the bank/aggregator must complete within 1 business day. Failed payment status updates (network errors, gateway timeouts) must be resolved within 4 hours through the automated reconciliation job. Challan (offline payment) verification must be completed by the finance officer within 2 working days of challan generation.

**SLA-006 — Notification Delivery SLA**
SMS notifications must be delivered within 2 minutes of the triggering event for 95% of messages. Email notifications must be delivered within 5 minutes for 95% of messages. In-portal notifications must appear within 30 seconds via WebSocket push. If SMS delivery fails after 3 retries (20-minute total window), an email fallback is triggered. Notification delivery status is logged and available to the Super Admin for audit.

---

### 3. Fee and Payment Policies

**FEE-001 — Challan Validity Period**
Offline payment challans generated by the portal are valid for 7 calendar days from the date and time of generation. A challan that has not been paid at an authorized bank or post office counter within 7 days is automatically expired by the nightly Celery task. Citizens receive an SMS and email reminder on Day 4 and Day 6 before expiry. An expired challan invalidates the associated application draft; the citizen must regenerate the challan and restart the submission process.

**FEE-002 — Payment Refund Policy**
Fee refunds are applicable under the following conditions: (a) department rejection of the application for reasons not attributable to the citizen (e.g., service suspended, eligibility criteria changed), (b) duplicate payment due to technical failure, (c) citizen withdrawal within 24 hours of submission before the application enters review. Refunds for condition (a) and (b) are processed within 7 working days to the original payment method. Refunds for condition (c) are processed within 5 working days. No refunds are issued for applications rejected due to incomplete documents or incorrect information provided by the citizen.

**FEE-003 — Automated Payment Reconciliation**
A Celery beat task runs daily at 02:00 IST to reconcile all portal payment records against ConnectIPS and Razorpay settlement files received via SFTP. Discrepancies (missing credits, excess debits) are flagged in the Finance Dashboard and trigger an alert to the Super Admin and the Finance Officer. Manual reconciliation must be completed within 2 business days of a flagged discrepancy. Reconciliation reports are archived for 7 years.

**FEE-004 — Fee Schedule Management**
Department Heads may request changes to fee schedules for their services through the Admin Console. Fee schedule changes require approval by the Super Admin and take effect only after a minimum 15-day notice period, during which existing applications retain the fee at the time of application creation (fee freeze on submission). Fee schedules are versioned in the database; historical fee records are never deleted. All fee schedule changes are logged in the audit trail with the approving admin's ID.

**FEE-005 — VAT (13%) and Statutory Levy Compliance**
All service fees displayed on the portal include applicable taxes (VAT (13%), stamp duty, cess) as determined by each department's fee schedule configuration. Payment receipts generated by the portal are VAT (13%)-compliant invoices with VAT (13%)IN, HSN/SAC codes, and itemized tax breakdowns where applicable. The portal does not process any fee collection outside of the approved payment gateways.

**FEE-006 — Partial Payment and Instalment Policy**
Service fees are collected in full at the time of application submission. Partial payments or instalments are not supported for any service currently on the catalog. In exceptional cases (court orders, welfare exemptions), the Department Head may manually waive fees with a documented justification, subject to Super Admin approval. All fee waivers are logged in the audit trail.

---

### 4. System Availability Policies

**AVAIL-001 — Scheduled Maintenance Windows**
Planned maintenance (patching, database upgrades, configuration changes) is scheduled during the approved maintenance window: **Sundays 02:00 – 06:00 IST**. Citizens are notified via a portal banner and SMS/email at least 48 hours before a maintenance window. Unplanned emergency maintenance (critical security patches, data integrity fixes) may be performed outside this window with immediate notification to the Super Admin and a post-incident review within 72 hours. During maintenance, the portal displays a static maintenance page served from S3/CloudFront.

**AVAIL-002 — Disaster Recovery (DR) Objective**
The portal is deployed across two AWS regions: the primary region (ap-south-1, Mumbai) and the DR region (ap-southeast-1, Singapore). The Recovery Time Objective (RTO) is 4 hours — the portal must be restored to full operational status within 4 hours of a primary region failure. The Recovery Point Objective (RPO) is 1 hour — a maximum of 1 hour of data may be lost in a disaster scenario. RDS PostgreSQL Multi-AZ with cross-region read replicas and automated backups (every 1 hour) supports this objective. Full DR failover drills are conducted quarterly.

**AVAIL-003 — Automated Failover and Self-Healing**
AWS ECS Fargate auto-scaling policies are configured to scale out when CPU utilization exceeds 70% for 2 consecutive minutes (scale-out threshold) and scale in when utilization falls below 30% for 10 minutes (scale-in threshold). Minimum 2 tasks per service are maintained at all times to ensure zero-downtime deployments. Amazon RDS Multi-AZ provides automated database failover within 60–120 seconds. ElastiCache Redis is configured with automatic failover using Redis Sentinel.

**AVAIL-004 — Backup and Restore Policy**
RDS PostgreSQL automated backups run every 1 hour to S3 in the primary region and are replicated to the DR region every 6 hours. Manual database snapshots are taken before every production deployment and retained for 30 days. S3 document vault data is protected by S3 Versioning and Cross-Region Replication to the DR region. Backup restore procedures are documented, tested quarterly, and results are reviewed by the Super Admin. Backup integrity is verified weekly via automated restore-and-hash-check jobs.

**AVAIL-005 — Incident Response and Escalation**
All production alerts are routed to PagerDuty with the following severity escalation:
- **P1 (Critical)**: Portal fully down or payment processing unavailable. On-call engineer paged immediately; Engineering Lead notified within 5 minutes; CTO / Programme Director notified within 15 minutes. Target resolution: 1 hour.
- **P2 (High)**: A major feature (document upload, application submission) unavailable for >10% of users. On-call engineer paged; target resolution: 4 hours.
- **P3 (Medium)**: Degraded performance, non-critical feature outage. Addressed during next business-hours shift; target resolution: 24 hours.
- **P4 (Low)**: Minor UI/UX issues, non-functional defects. Triaged in the next sprint planning; target resolution: 1 week.
All P1 and P2 incidents have mandatory post-incident reviews (PIR) documented within 5 business days.
