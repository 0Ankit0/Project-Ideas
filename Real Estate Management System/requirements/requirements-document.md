# Requirements Document — Real Estate Management System

**Version:** 1.0  
**Date:** 2025-01  
**Status:** Approved  
**Authors:** Product Management, Architecture Team  

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Stakeholders](#stakeholders)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [Constraints](#constraints)
6. [Assumptions](#assumptions)

---

## System Overview

The Real Estate Management System (REMS) is a cloud-native, multi-tenant SaaS platform that automates the full operational lifecycle of real estate property management. The system enables property management companies and independent landlords to manage properties from listing through lease termination, handling tenant screening, rent collection, maintenance coordination, and owner financial reporting in a single integrated platform.

The platform operates across three primary property categories:
- **Residential:** Single-family homes, condominiums, townhouses, multi-family buildings, apartments
- **Commercial:** Office spaces, retail storefronts, industrial/warehouse, mixed-use developments
- **Short-term / Furnished:** Serviced apartments and furnished units (with weekly/monthly billing)

The system supports multi-currency operations, multi-jurisdiction compliance rules, and role-based access control across all features.

---

## Stakeholders

| Stakeholder | Role | Primary Concern |
|-------------|------|-----------------|
| Property Manager | System operator | Efficiency, automation, compliance |
| Tenant | End user | Transparency, convenience, responsiveness |
| Property Owner | Financial stakeholder | Returns, reporting, occupancy |
| Contractor | External partner | Work orders, payment, communication |
| System Administrator | Platform operator | Security, uptime, integrations |
| Compliance Officer | Governance | Fair Housing, GDPR, PCI DSS |

---

## Functional Requirements

### FR Domain: Property Management

**FR-01 — Property Registration**  
The system shall allow property managers to create and manage property records including address, type, size, zoning, construction year, tax parcel ID, and owner association.

**FR-02 — Property Unit Management**  
The system shall support hierarchical property structures: Property → Floor → Unit → Room, with each unit having type, area (sq ft/m²), bedroom/bathroom count, and current status (vacant, listed, leased, maintenance).

**FR-03 — Amenity Management**  
The system shall allow associating a configurable list of amenities (parking, gym, pool, elevator, laundry, pet-friendly, EV charging, rooftop access) to properties and individual units.

**FR-04 — Property Search and Filtering**  
The system shall expose a searchable property index with filters by city, zip code, property type, unit type, rent range, availability date, and amenity. Search results shall be paginated and sortable.

**FR-05 — Multi-Company Hierarchy**  
The system shall support a Company → Agency → Property Manager hierarchy with role-based data isolation ensuring managers can only access properties within their assigned portfolio.

**FR-06 — Property Document Storage**  
The system shall support storing and retrieving property-level documents including deeds, insurance certificates, inspection reports, and floor plans, with version control and access audit logging.

### FR Domain: Listing Management

**FR-07 — Listing Creation**  
The system shall allow creating rental listings linked to a specific property unit, including title, description, rent price, available date, lease term options, and pet/smoking policy.

**FR-08 — Listing Photo Management**  
The system shall support uploading up to 50 photos per listing, stored in cloud object storage (S3), served via CDN. Photos shall be automatically resized to web, thumbnail, and print quality. Each photo shall include a caption and room category tag.

**FR-09 — Listing Publication and Syndication**  
The system shall publish active listings to integrated external portals: Zillow, Apartments.com, and Trulia. Syndication shall be triggered automatically within 15 minutes of a listing being set to active. Deactivation shall propagate within 30 minutes.

**FR-10 — Listing Price History**  
The system shall maintain a complete audit trail of listing price changes including the old price, new price, effective date, and the manager who made the change.

**FR-11 — Listing Status Lifecycle**  
Listing states shall follow: Draft → Active → ApplicationPending → Rented → Inactive. The system shall prevent a listing from being set to Rented without a signed lease in place.

### FR Domain: Tenant Management

**FR-12 — Tenant Profile Management**  
The system shall maintain tenant profiles including personal details, employment information, emergency contacts, identification documents, vehicle information, and rental history. PII fields shall be encrypted at rest.

**FR-13 — Tenant Application Submission**  
The system shall provide an online application form for prospective tenants including personal details, income verification, rental history, references, pet information, and required document uploads (photo ID, pay stubs, bank statements).

**FR-14 — Background Check Integration**  
Upon application submission, the system shall automatically initiate a background check via Checkr API covering criminal history, eviction records, and sex offender registry. Results shall be stored encrypted and associated with the application.

**FR-15 — Credit Check Integration**  
The system shall integrate with Experian Connect API to retrieve credit reports and scores for applicants. A soft pull shall be used during pre-screening; a hard pull shall only be initiated upon explicit tenant consent.

**FR-16 — Application Review Workflow**  
The system shall provide a property manager workflow for reviewing applications showing all screening results, income-to-rent ratio, and a recommendation score. Managers shall be able to approve, reject, or request additional information.

**FR-17 — Application Status Notifications**  
The system shall automatically notify applicants of status changes (received, under review, approved, rejected) via email and SMS within 5 minutes of status change.

**FR-18 — Fair Housing Compliance Controls**  
The system shall enforce Fair Housing Act compliance by logging rejection reasons against a compliant code list, providing fair housing training resources, and preventing discriminatory fields from being used as application filters.

### FR Domain: Lease Management

**FR-19 — Lease Creation from Template**  
The system shall generate leases from configurable state-specific templates, populating tenant, unit, and financial details automatically. Property managers shall be able to add, remove, or modify standard clauses.

**FR-20 — Digital Lease Signing via DocuSign**  
The system shall integrate with DocuSign eSignature API to enable all parties (tenant(s), co-signers, property manager) to sign leases electronically. The system shall track signing status per party and store the completed signed document.

**FR-21 — Lease Versioning**  
The system shall maintain version history for every lease amendment, storing the diff, the reason for change, and signatures for each version. A lease version chain shall be auditable end-to-end.

**FR-22 — Lease Renewal Management**  
The system shall automatically generate lease renewal offers 90, 60, and 30 days before expiration with configurable notice periods per jurisdiction. Renewal terms shall be negotiable before the tenant accepts.

**FR-23 — Lease Termination**  
The system shall support both mutual-agreement and unilateral (eviction notice pathway) terminations with prorated rent calculation for mid-month terminations, early termination fee assessment, and automatic security deposit disposition workflow.

**FR-24 — Lease Clause Library**  
The system shall maintain a library of pre-approved lease clauses (pet policy, smoking policy, parking allocation, utility responsibility, subletting restrictions) that can be selected and customized during lease creation.

### FR Domain: Rent & Payment Management

**FR-25 — Rent Schedule Setup**  
The system shall allow configuring rent schedules per lease including base rent, due date (1st, 15th, or custom), grace period (1–7 days, jurisdictional default), prorated first/last month, and rent escalation schedule.

**FR-26 — Automated Rent Invoice Generation**  
The system shall automatically generate rent invoices on a configurable schedule (default: 5 days before due date), including base rent, recurring charges (parking, pet fee, storage), and any outstanding balances from prior periods.

**FR-27 — Online Rent Payment Collection**  
The system shall accept rent payments via ACH bank transfer and credit/debit card via Stripe. Tenants shall be able to set up autopay (ACH recommended for cost). Payment receipts shall be emailed within 60 seconds of processing.

**FR-28 — Partial Payment Handling**  
The system shall accept partial payments and apply them in the following order: outstanding fees first, then oldest invoice principal. The remaining balance shall be tracked and a new invoice issued at next billing cycle.

**FR-29 — Late Fee Calculation**  
The system shall automatically calculate and apply late fees after the grace period expires, using a configurable structure: flat fee, percentage of monthly rent, or daily accrual, subject to jurisdictional maximums. Late fee invoices shall be generated separately from rent invoices.

**FR-30 — Security Deposit Management**  
The system shall track security deposit collection, holding in a designated escrow account, and return/refund workflows. Itemized deductions shall be documented with descriptions and supporting photos. Refund shall be processed within the jurisdiction-mandated window (21–45 days typical).

**FR-31 — NSF / Returned Payment Processing**  
When a payment is returned (NSF, ACH reversal), the system shall automatically reverse the payment, reopen the invoice, apply an NSF fee, and notify the tenant. Payment method shall be flagged for manager review.

**FR-32 — Ledger and Reconciliation**  
The system shall maintain a per-lease financial ledger tracking all charges, payments, credits, and adjustments in double-entry format. Ledger exports shall be available in CSV and QuickBooks-compatible format.

### FR Domain: Maintenance Management

**FR-33 — Tenant Maintenance Request Submission**  
The system shall provide a tenant portal (web and mobile) for submitting maintenance requests with description, category (plumbing, electrical, HVAC, pest, appliance, structural), priority indicator, and photo/video attachments.

**FR-34 — Maintenance Priority Classification**  
The system shall classify maintenance requests as Emergency (life/safety), Urgent (habitability-affecting), Routine, or Preventive. Classification may be auto-suggested based on category and keywords, with manager override.

**FR-35 — Contractor Assignment**  
The system shall allow assigning maintenance requests to internal staff or external contractors from a managed contractor database. Assignment triggers email/SMS notification to the contractor with work order details and access instructions.

**FR-36 — Work Order Tracking**  
The system shall track work order status from Submitted → Assigned → In Progress → Completed → Closed. Each status transition shall record the actor, timestamp, and optional notes. Tenants shall receive status update notifications.

**FR-37 — Maintenance Photo Documentation**  
Contractors and property managers shall be able to attach before/after photos to maintenance requests. Photos shall be stored in S3 and linked to the maintenance record for inspection and insurance purposes.

**FR-38 — Maintenance SLA Monitoring**  
The system shall monitor response and resolution times against configured SLAs per priority level and flag overdue requests to supervisors. Emergency requests: 4-hour response; Urgent: 24-hour; Routine: 5 business days.

**FR-39 — Contractor Invoice and Payment**  
The system shall allow contractors to submit invoices for completed work. Property managers shall approve or dispute invoices. Approved invoices shall be queued for payment and export to accounting software.

### FR Domain: Property Inspections

**FR-40 — Inspection Scheduling**  
The system shall allow scheduling inspections with configurable types: move-in, move-out, mid-lease, seasonal, and drive-by. Inspection scheduling shall notify tenants with legally required notice (24–48 hours per jurisdiction).

**FR-41 — Digital Inspection Checklists**  
The system shall provide configurable digital checklists per property type and inspection type. Each checklist item shall have a condition rating (Excellent, Good, Fair, Poor, Damaged) and photo attachment capability.

**FR-42 — Inspection Report Generation**  
Upon inspection completion, the system shall generate a PDF inspection report with all item ratings, photos, notes, inspector signature, and tenant acknowledgment option. Reports shall be stored in document management.

**FR-43 — Inspection-to-Deposit Workflow**  
Move-out inspection results shall automatically initiate the security deposit disposition workflow, flagging damaged items for deduction assessment and pre-populating the deduction form with inspection line items.

### FR Domain: Owner Management & Reporting

**FR-44 — Owner Portal**  
The system shall provide owners with a read-only portal showing real-time portfolio overview: occupancy rates, current leases, upcoming vacancies, maintenance summaries, and financial performance.

**FR-45 — Owner Statement Generation**  
The system shall generate monthly owner statements per property showing: gross rent collected, management fees, maintenance expenses, utility costs, other charges, and net owner distribution. Statements shall be PDF-ready and emailed automatically.

**FR-46 — Management Fee Calculation**  
The system shall calculate management fees based on configurable structures: flat monthly fee, percentage of collected rent, or tiered models. Fees shall be deducted from owner distributions automatically.

**FR-47 — Year-End Tax Reporting**  
The system shall generate 1099-MISC forms for contractors paid over $600/year and provide owner income summaries in IRS-compatible format. QuickBooks export shall include categorized expense data.

### FR Domain: Utility Management

**FR-48 — Utility Account Tracking**  
The system shall track utility accounts per unit (electricity, gas, water, sewer, trash, internet) including provider name, account number, billing cycle, and responsibility assignment (landlord vs. tenant).

**FR-49 — Utility Sub-Meter Billing**  
For properties with sub-meters, the system shall accept meter reading imports (manual entry or API feed), calculate consumption per unit, apply utility rates, and generate utility invoices as part of the rent billing cycle.

**FR-50 — Utility Reconciliation**  
The system shall reconcile utility bills from providers against sub-meter calculations, flagging discrepancies greater than 5% for review. Reconciliation reports shall be available monthly.

### FR Domain: Document Management

**FR-51 — Document Repository**  
The system shall maintain a document repository supporting property, lease, tenant, and maintenance documents with versioning, tagging, and role-based access. Supported formats: PDF, DOCX, XLSX, JPEG, PNG, MP4.

**FR-52 — Document Expiry Alerts**  
The system shall track document expiry dates (insurance certificates, contractor licenses, lease agreements) and generate alerts 90 days, 30 days, and 7 days before expiry.

**FR-53 — Audit Trail**  
All document views, downloads, uploads, and deletions shall be logged to an immutable audit trail with user, timestamp, IP address, and action type. Audit logs shall be retained for 7 years.

### FR Domain: Analytics & Reporting

**FR-54 — Occupancy Analytics**  
The system shall provide real-time and historical occupancy rate dashboards by property, portfolio, geography, and property type. Vacancy duration and turn cost analysis shall be included.

**FR-55 — Revenue Analytics**  
The system shall track revenue metrics including: gross potential rent (GPR), effective gross income (EGI), net operating income (NOI), delinquency rate, collection rate, and maintenance cost as % of revenue.

---

## Non-Functional Requirements

**NFR-01 — Availability**  
The system shall achieve 99.9% monthly uptime (≤43.8 minutes downtime/month) for core services (API, payments, lease signing). Planned maintenance windows shall not exceed 4 hours per quarter and shall occur between 02:00–06:00 UTC on Sundays.

**NFR-02 — Performance: API Response Time**  
95th-percentile API response time shall be ≤300ms for read operations and ≤800ms for write operations under normal load (up to 500 concurrent users). Search endpoints shall respond within 500ms at the 95th percentile.

**NFR-03 — Performance: Payment Processing**  
Stripe payment processing confirmations shall complete within 5 seconds for card payments and 3 business days for ACH transfers. Payment status updates shall be delivered to tenants within 60 seconds.

**NFR-04 — Scalability**  
The system shall scale horizontally to support 500,000 managed units, 2,000,000 active tenants, and 10,000 concurrent sessions without degradation. Database read replicas and Kafka partitioning shall enable linear scaling.

**NFR-05 — Data Durability**  
Financial data (invoices, payments, ledger entries) shall be stored with 99.999999999% (11-nines) durability using multi-region S3 storage. Database backups shall occur every 6 hours with point-in-time recovery for 30 days.

**NFR-06 — Security: Authentication**  
All API endpoints shall require authentication via JWT (access token 15-minute expiry) with refresh tokens (30-day expiry). Multi-factor authentication (TOTP or SMS OTP) shall be required for property manager and admin accounts.

**NFR-07 — Security: Authorization**  
The system shall enforce row-level security in PostgreSQL ensuring users can only access records within their authorized company/agency scope. All authorization checks shall be logged.

**NFR-08 — Security: Encryption**  
All PII fields (SSN, date of birth, bank account numbers) shall be encrypted at rest using AES-256 with key rotation annually. All data in transit shall use TLS 1.3 minimum.

**NFR-09 — Security: PCI DSS**  
Card payment data shall never be stored in REMS databases. Stripe.js client-side tokenization shall be used. The system shall maintain PCI DSS SAQ A compliance.

**NFR-10 — Compliance: Fair Housing**  
The system shall enforce Fair Housing Act controls preventing discriminatory filtering and logging all application rejection reasons against a compliant taxonomy. Annual compliance audits shall be supported.

**NFR-11 — Compliance: GDPR / CCPA**  
The system shall support tenant PII deletion requests (right to erasure) with a 30-day processing window, data portability export (JSON), and consent management for marketing communications.

**NFR-12 — Compliance: Financial Regulations**  
Security deposit accounting shall comply with state-specific trust account requirements. Owner distributions shall maintain audit trails compliant with property management licensing board regulations.

**NFR-13 — Observability**  
All services shall expose Prometheus metrics, structured JSON logs to CloudWatch/Datadog, and distributed traces via OpenTelemetry. Service health endpoints shall respond within 50ms.

**NFR-14 — Disaster Recovery**  
Recovery Time Objective (RTO): 4 hours. Recovery Point Objective (RPO): 1 hour. Failover shall be tested quarterly through automated game day exercises. Database failover shall be automatic via RDS Multi-AZ.

**NFR-15 — Maintainability**  
Code coverage for unit tests shall be ≥80% across all services. Integration test coverage shall cover all critical user flows. Technical debt ratio (SonarQube) shall remain below 5%.

**NFR-16 — Internationalization**  
The system shall support multi-currency display and storage (ISO 4217 codes). Date/time formatting shall respect locale. The codebase shall be prepared for UI string extraction (i18n framework: react-i18next).

**NFR-17 — Accessibility**  
Tenant-facing web interfaces shall conform to WCAG 2.1 Level AA. Screen reader compatibility shall be tested quarterly.

**NFR-18 — API Versioning**  
All public APIs shall be versioned (v1, v2 prefix). Breaking changes shall require a new major version with a minimum 12-month deprecation period for prior versions.

**NFR-19 — Integration Resilience**  
External service integrations (Checkr, DocuSign, Stripe, SendGrid, Zillow) shall implement circuit breakers with exponential backoff retry. Failed integrations shall not block core platform operations; queued retry with DLQ shall be used.

**NFR-20 — Audit Logging**  
All state-changing operations on lease, payment, and tenant records shall produce an immutable audit log entry with: actor identity, action, affected resource ID, before/after state, timestamp, and source IP. Logs retained 7 years.

**NFR-21 — Multi-Tenancy**  
The system shall enforce strict tenant data isolation at the database row-level security (RLS) layer. Cross-tenant data leakage shall be prevented both in API responses and in async job processing.

**NFR-22 — Mobile Responsiveness**  
The tenant portal shall be fully functional on iOS 16+ and Android 13+ mobile browsers. Maintenance request submissions (including photo capture) shall work on mobile without native app installation.

---

## Constraints

1. **Regulatory:** Security deposit handling must comply with applicable state laws governing escrow accounts, interest accrual, and return timeframes. The system must support configurable jurisdiction-specific rules.
2. **Third-Party APIs:** Background check and credit check integration is limited by Checkr and Experian API rate limits and SLAs. The system shall implement graceful degradation when these services are unavailable.
3. **Data Residency:** Tenant PII shall be stored in AWS us-east-1 (primary) and us-west-2 (DR) only. No PII shall traverse third-party services beyond the minimum required for background/credit checks.
4. **DocuSign:** E-signature envelopes are subject to DocuSign plan limits. The system shall monitor envelope consumption and alert administrators at 80% of plan limit.
5. **Payment Processing:** PCI DSS compliance mandates that raw card data never touches REMS servers. All card interactions must occur via Stripe.js or Stripe Elements.
6. **Financial Calculations:** All monetary calculations shall use integer arithmetic (cents) to avoid floating-point rounding errors. Currency conversion rates shall be sourced from European Central Bank daily feed.

---

## Assumptions

1. Property managers will have reliable internet connectivity; offline operation is not a core requirement for manager workflows (though tenant maintenance submission shall support offline queuing).
2. All properties are located in the United States (initial launch); international expansion (Canada, UK) is planned for v2.
3. The platform will integrate with a single payment processor (Stripe) initially; multi-processor routing is a future enhancement.
4. Lease template library will be seeded by legal team per state before launch; self-service template creation is a Phase 2 feature.
5. Owner users access the portal read-only; write access for owners is not in scope for v1.
6. Background check consent collection from applicants is handled within the tenant application portal; REMS does not separately manage FCRA adverse action letters (handled by Checkr).
7. QuickBooks integration uses OAuth 2.0 and is configured per company; a single QuickBooks account per property management company is assumed for v1.
