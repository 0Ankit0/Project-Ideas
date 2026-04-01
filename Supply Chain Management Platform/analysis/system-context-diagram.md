# System Context Diagram — Supply Chain Management Platform

## Purpose and Scope

This document provides a C4 Model Level 1 (System Context) view of the Supply Chain Management
Platform (SCMP). It establishes the outermost system boundary, identifies every human actor who
interacts directly with the platform, and catalogues all external software systems that either
supply data to or consume data from the platform. The intended audience includes enterprise
architects, solution designers, integration engineers, information-security teams, and external
auditors who need a complete map of the platform's external surface area without requiring
knowledge of its internal component structure. This context view is the foundation from which
all subsequent C4 Level 2 (Container) and Level 3 (Component) diagrams are derived.

The scope deliberately avoids prescribing internal technology choices, deployment topology, or
service decomposition — those concerns belong in container and component diagrams. Instead, this
document answers three fundamental questions: who uses the system, what external systems does it
depend on or expose services to, and what data and messages cross each boundary. All integration
protocols, data classifications, security trust zones, and compliance obligations attached to
each data crossing are captured here to support threat modelling under the STRIDE methodology
and to satisfy data-flow mapping requirements for ISO 27001 Annex A.13, SOC 2 Type II CC6,
GDPR Article 30 records of processing activities, and financial-controls frameworks such as
COSO and COBIT 2019.

---

## C4 Level 1 — System Context

```mermaid
C4Context
    title System Context — Supply Chain Management Platform

    Enterprise_Boundary(b0, "Enterprise Boundary") {
        Person(procMgr, "Procurement Manager",
            "Creates PRs, approves POs within delegated authority, monitors open-order backlog,
             manages supplier delivery performance")
        Person(catMgr, "Category Manager",
            "Owns spend-category sourcing strategy, designs RFQ/RFP events,
             evaluates bids, negotiates and activates contracts")
        Person(whMgr, "Warehouse Manager",
            "Schedules dock appointments, physically receives goods against ASNs,
             records GRNs, triggers quality inspections, initiates RTVs")
        Person(apClerk, "AP Clerk",
            "Processes inbound supplier invoices, reviews three-way match results,
             resolves exceptions and disputes, releases payment batches")
        Person(finDir, "Finance Director",
            "Approves high-value payment batches above CFO threshold,
             reviews working-capital dashboards, authorises period-end reconciliations")
        Person(sysAdmin, "System Administrator",
            "Provisions users, assigns RBAC roles, configures approval workflows,
             manages API credentials and TLS certificates, monitors platform health")

        System(scmp, "Supply Chain Management Platform",
            "End-to-end supply chain operations: procure-to-pay, source-to-contract,
             supplier lifecycle management, goods receipt, invoice processing,
             and financial reconciliation")
    }

    Person_Ext(supplRep, "Supplier Representative",
        "External supplier employee who views POs, submits bids,
         uploads invoices, and monitors payment status via self-service portal")

    System_Ext(erp, "ERP System (SAP / Oracle)",
        "Financial system of record: GL account master, cost-centre hierarchy,
         approved budgets, and ledger for GR accrual and invoice payment journals")
    System_Ext(bank, "Banking / Payment Gateway",
        "Executes outbound payment instructions via SWIFT MT103, ISO 20022 pain.001,
         ACH, or SEPA; returns settlement confirmations and debit advices")
    System_Ext(edi, "EDI Network (AS2 / SFTP)",
        "Carries EDIFACT and X12 trade documents — POs, acknowledgements,
         ASNs, and invoices — between platform and EDI-capable suppliers")
    System_Ext(risk, "Credit & Risk Scoring Service",
        "Provides supplier credit scores, insolvency-probability models,
         OFAC/UN sanctions screening results, adverse-media flags, and ESG ratings")
    System_Ext(customs, "Regulatory / Customs Portal",
        "Accepts electronic import/export declarations; returns tariff classifications,
         duty assessments, clearance decisions, and restricted-party flags")
    System_Ext(notify, "Email / Notification Service",
        "Delivers transactional emails, in-app push notifications, and SMS alerts
         triggered by platform workflow events")
    System_Ext(dms, "Document Management System",
        "Enterprise content repository for long-term archival and retrieval of
         contracts, certificates, signed GRNs, and audit evidence packages")
    System_Ext(idp, "Identity Provider (SSO)",
        "Federates authentication via SAML 2.0 for internal users and OIDC for
         supplier portal users; provides identity-attribute assertions")

    Rel(procMgr, scmp, "Creates PRs, approves POs, monitors orders, reviews supplier KPIs")
    Rel(catMgr, scmp, "Manages sourcing events, evaluates bids, awards contracts")
    Rel(whMgr, scmp, "Records GRNs, schedules docks, triggers inspections, raises RTVs")
    Rel(apClerk, scmp, "Processes invoices, resolves exceptions, releases payment batches")
    Rel(finDir, scmp, "Approves CFO-threshold batches, reviews dashboards")
    Rel(sysAdmin, scmp, "Manages users, roles, workflows, integrations, and config")
    Rel(supplRep, scmp, "Views POs, submits bids, uploads invoices, tracks payments")

    Rel(scmp, erp, "Budget check (real-time); GRN + invoice journals; GL/vendor sync (nightly)",
        "REST / SAP IDoc / Oracle BPEL")
    Rel(scmp, bank, "Payment instruction files; debit confirmations; SWIFT GPI tracking",
        "ISO 20022 pain.001 / SFTP-PGP / camt.054")
    Rel(scmp, edi, "Outbound: ORDERS / ORDCHG; Inbound: ORDRSP / DESADV / INVOIC",
        "AS2 + S/MIME / EDIFACT D.96A / X12 5010")
    Rel(scmp, risk, "Onboarding risk check; quarterly rescoring; real-time sanctions webhook",
        "REST JSON / OAuth 2.0 / Webhook")
    Rel(scmp, customs, "Import/export declarations; clearance status; duty assessments",
        "HTTPS REST / SOAP / mTLS")
    Rel(scmp, notify, "Approval requests, PO dispatch, GRN confirm, payment advice",
        "SMTP TLS / REST API")
    Rel(scmp, dms, "Archive contracts/GRNs/invoices; retrieve on demand",
        "CMIS 1.1 / REST / mTLS")
    Rel(scmp, idp, "SP-initiated SSO; SAML assertion validation; OIDC token exchange; SLO",
        "SAML 2.0 / OIDC / OAuth 2.0")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

---

## Actor and System Descriptions

### Internal Users

**Procurement Manager**
- Type: Internal Person
- Role: Manages day-to-day purchasing operations, maintains active supplier relationships,
  and ensures all purchase orders comply with the procurement policy and delegated-authority matrix.
- Key interactions: Creates and submits purchase requisitions with full GL coding; approves POs
  within their delegated authority band (typically up to $50,000); monitors open-order status,
  overdue deliveries, and receipt confirmations; reviews supplier performance scorecards generated
  from GRN quality acceptance rates and on-time delivery metrics.

**Category Manager**
- Type: Internal Person
- Role: Owns the strategic sourcing function for one or more assigned spend categories and drives
  cost reduction through competitive sourcing events and long-term framework agreements.
- Key interactions: Designs weighted-criteria RFQ/RFP evaluation templates; invites pre-qualified
  suppliers to sourcing events; manages the bid submission window; scores received bids and
  generates award recommendations; negotiates contract terms; activates approved price lists and
  blanket orders in the system.

**Warehouse Manager**
- Type: Internal Person
- Role: Oversees physical inbound-goods handling at one or more stocking locations and maintains
  GRN accuracy for three-way matching purposes.
- Key interactions: Schedules dock appointments against confirmed supplier ASNs; supervises
  physical count verification; records GRNs with actual quantities, lot numbers, and batch
  attributes; initiates quality holds; raises return-to-vendor requests for non-conforming
  deliveries and tracks credit-note receipt.

**AP Clerk**
- Type: Internal Person
- Role: Manages the end-to-end accounts payable workflow for all supplier invoices from receipt
  to payment scheduling.
- Key interactions: Monitors invoices at every processing stage; reviews automated three-way
  match results and exception flags; raises and resolves invoice disputes with suppliers;
  prepares payment run proposals; applies supplier credit notes; uploads corrected invoices
  following PO amendments.

**Finance Director**
- Type: Internal Person
- Role: Provides executive financial governance over significant payment outflows and
  period-end AP integrity.
- Key interactions: Approves payment batches exceeding the CFO monetary threshold; reviews
  daily cash-flow impact and days-payable-outstanding dashboards; signs off on the period-end
  reconciliation report comparing SCMP AP balances to the ERP general ledger before financial
  close.

**System Administrator**
- Type: Internal Person
- Role: Ensures platform operational integrity, security posture, and integration reliability.
- Key interactions: Provisions and deprovisions user accounts; assigns and audits RBAC role
  profiles; configures multi-level approval-threshold rules; manages OAuth 2.0 client
  credentials and API keys; monitors integration error queues and dead-letter topics; performs
  data corrections under a four-eyes change-approval procedure.

### External Users

**Supplier Representative**
- Type: External Person
- Role: Supplier-side employee who interacts through the self-service portal to manage the
  commercial relationship with the buying organisation.
- Key interactions: Views issued purchase orders and amendments; submits competitive bids on
  active sourcing events; uploads invoice PDFs or structured XML e-invoices; tracks invoice
  processing stage (received, matched, approved, scheduled, paid); responds to compliance data
  requests and document-renewal reminders.

### External Systems

**ERP System (SAP / Oracle)**
- Type: External System
- Role: Financial system of record for all journal accounting, budget control, and vendor
  master management.
- Key data flows: Provides GL account codes, cost-centre tree, and real-time available-budget
  balances to SCMP for PR/PO budget validation. Receives goods-receipt accrual journals and
  invoice-payment journals from SCMP after each approval event. Supplies vendor master records
  including bank account, payment terms, and currency.

**Banking / Payment Gateway**
- Type: External System
- Role: Executes bank payments on behalf of the company across multiple payment rails.
- Key data flows: Receives structured payment files (ISO 20022 pain.001 or SWIFT MT101) after
  finance approval; executes transfers via SWIFT, SEPA, ACH, or faster-payment rails; returns
  camt.054 debit confirmations and SWIFT GPI tracking events used to update payment records.

**EDI Network (AS2 / SFTP)**
- Type: External System
- Role: Standards-based B2B document-exchange backbone for high-volume EDI-capable suppliers.
- Key data flows: Carries EDIFACT ORDERS and ORDCHG outbound (POs and amendments). Receives
  ORDRSP (acknowledgements), DESADV (advance shipment notices), and INVOIC (invoices) inbound.
  Enforces AS2 with S/MIME signing and synchronous MDN receipts for non-repudiation.

**Credit & Risk Scoring Service**
- Type: External System
- Role: Supplier financial and reputational risk intelligence provider.
- Key data flows: Returns credit score (0–1000), payment-behaviour index, 1-year insolvency
  probability, OFAC/EU/UN sanctions match flag, adverse-media summary, and ESG tier (A–E).
  Pushes real-time webhook alerts on new sanctions events.

**Regulatory / Customs Portal**
- Type: External System
- Role: Government or third-party customs broker API for cross-border trade compliance.
- Key data flows: Accepts HS-code-enriched shipment declarations at PO placement for
  cross-border orders; returns customs entry reference, assessed duty amount, clearance
  decision (cleared / held / refused), and restricted-party or export-licence flags.

**Email / Notification Service**
- Type: External System
- Role: Transactional notification delivery platform.
- Key data flows: Delivers formatted HTML emails and plaintext SMS messages for workflow
  events (approval requests, PO dispatch, GRN notifications, payment advices); supports
  template-based messaging with merge variables; provides delivery-status tracking and
  bounce management.

**Document Management System**
- Type: External System
- Role: Enterprise content management repository for long-term document retention.
- Key data flows: Stores executed contracts (PDF/A-3), signed GRN acknowledgements, approved
  invoices, supplier certificates, and audit evidence bundles; supports metadata-driven
  retrieval by document type, supplier ID, PO number, or date range.

**Identity Provider (SSO)**
- Type: External System
- Role: Centralised authentication authority and attribute-assertion service.
- Key data flows: Handles SAML 2.0 SP-initiated SSO for internal employees via corporate
  Active Directory federation; OIDC Authorization Code with PKCE for supplier portal users;
  asserts attributes: sub, email, display_name, department, cost_centre, approval_limit_band,
  role_groups, authentication_method, authentication_time.

---

## System Boundary

### Inside the Platform Boundary

The SCMP encapsulates all transactional and analytical capabilities required to manage the full
procure-to-pay and source-to-contract lifecycles.

**Procurement Operations**

- Purchase requisition entry with full GL account and cost-centre coding
- Real-time budget availability check against ERP-sourced budget data at PR submission
- Configurable multi-level approval routing driven by rules across requester department,
  spend category, commodity code, and PR total value
- Automated PR-to-PO conversion with sequential PO numbering and line-item inheritance
- PO transmission to suppliers via EDI, email-PDF attachment, or portal download
- PO amendment handling with automatic re-approval triggers where the delta exceeds a
  configurable threshold
- Open-order monitoring dashboard with configurable overdue-delivery alerting

**Strategic Sourcing**

- RFQ, RFP, and sealed reverse-auction event lifecycle management
- Supplier invitation with optional NDA gate requiring digital acknowledgement
- Configurable bid-submission windows with automatic late-bid rejection
- Multi-criteria weighted scoring templates with per-evaluator assignment
- Award recommendation report generation with ranked scoring breakdown
- Contract authoring from an approved clause library with redline and version tracking
- E-signature collection through an integrated DocuSign / Adobe Sign adapter
- Contract lifecycle management: version history, amendment tracking, renewal reminders,
  expiry alerting
- Activation of framework agreements, blanket purchase orders, and electronic price catalogues

**Supplier Lifecycle Management**

- Supplier self-registration portal with guided onboarding wizard
- Compliance document collection: tax registration, insurance certificates, ISO certifications,
  financial statements, beneficial-ownership declarations
- Automated document-expiry monitoring with renewal-request notifications
- Integration with credit and risk scoring service at onboarding and quarterly review
- Human-review qualification workflow with configurable stage gates
- Approved-supplier list (ASL) and category-assignment management
- Supplier performance scorecard calculation from GRN quality acceptance rates and OTD ratios
- Periodic re-qualification and structured offboarding workflows

**Inbound Goods Management**

- ASN receipt and PO-line validation; out-of-tolerance quantity alerting
- Dock appointment scheduling linked to confirmed ASN delivery dates
- GRN creation capturing actual quantities, lot numbers, serial numbers, and batch attributes
- Quality inspection trigger routing based on item-level inspection plans (100%, AQL, skip-lot)
- Quality pass/fail recording with supporting test-result attachments
- Quarantine stock status management and disposition workflow
- Return-to-vendor (RTV) initiation with document generation and credit-note tracking

**Accounts Payable and Invoice Processing**

- Multi-channel invoice ingestion: supplier portal upload, EDI INVOIC, email OCR/IDP extraction
- Invoice format validation: PEPPOL BIS 3.0, UBL 2.1, EDIFACT INVOIC D.96A, extracted-PDF
- Duplicate invoice detection via fuzzy matching on invoice number, supplier ID, and amount
- Three-way match engine: PO line ↔ GRN line ↔ invoice line with configurable per-line tolerances
- Auto-approval for fully matched invoices within tolerance; exception routing for discrepancies
- Invoice dispute management with supplier collaboration thread and resolution SLA tracking
- Credit-note application; payment scheduling; ISO 20022 bank-file generation

**Reporting and Analytics**

- Real-time operational dashboards: procurement KPIs, supplier performance, exception queues,
  cash-flow forecast
- Scheduled period-end reports: AP accrual, spend analysis by category and cost centre,
  purchase-price variance, savings tracking
- Ad-hoc data export in CSV and XLSX formats
- Full audit-log viewer: field-level before/after change history, user identity, timestamp,
  source IP, and correlation ID

### Outside the Platform Boundary

| Excluded Capability | Responsible External System | Rationale |
|---|---|---|
| General ledger maintenance and statutory reporting | ERP System (SAP / Oracle) | ERP is the single financial source of truth; SCMP posts journals but does not own the ledger |
| Physical payment execution | Banking / Payment Gateway | SCMP generates and authorises files but does not directly move funds |
| Outbound logistics and transport management | Third-party TMS | Transportation planning is out of scope; SCMP receives ASNs but does not route carriers |
| Finished-goods inventory management | Dedicated WMS | Post-GRN stock movements and pick/pack operations are handled by a separate WMS |
| Complex VAT/GST computation | External tax engine (Vertex / Avalara) | Multi-jurisdiction tax calculations are delegated to a specialised tax engine via API |
| HR master data and employee directory | HR System → IdP federation | Employee records originate in HR; federated into SCMP via SAML attribute assertions |
| E-signature orchestration | DocuSign / Adobe Sign (adapter) | The e-sign platform is invoked by SCMP for contract execution; it is not part of SCMP |
| Corporate card and travel expense management | Separate T&E platform | Not in scope for supply chain procurement |

---

## Integration Points Summary

| External System | Protocol / Standard | Direction | Frequency / Trigger | Key Data Exchanged |
|---|---|---|---|---|
| ERP System | SAP RFC/BAPI; Oracle REST; SAP IDoc; nightly SFTP extract | Bidirectional | Real-time: budget check, GRN journal, invoice journal. Nightly: GL master, cost centres, vendor master | → ERP: GR accrual journal, AP payment journal, PO commitments. ← ERP: GL codes, cost-centre tree, budgets, vendor IDs |
| Banking / Payment Gateway | ISO 20022 pain.001; SWIFT MT101; camt.054; SFTP-PGP-4096 | Outbound: files. Inbound: confirmations | Twice-daily payment runs (08:00, 14:00); real-time GPI webhooks | → Bank: payee name, IBAN, BIC, currency, amount, value date, reference. ← Bank: debit confirmations, rejection advices, GPI events |
| EDI Network | EDIFACT D.96A (ORDERS, ORDCHG, ORDRSP, DESADV, INVOIC); X12 5010 (850, 860, 855, 856, 810); AS2/S-MIME; MDN; SFTP fallback | Bidirectional | Event-driven per transaction; MDN within 60 s; SFTP poll every 15 min | → EDI: POs and amendments. ← EDI: acknowledgements, ASNs, invoices |
| Credit & Risk Scoring | HTTPS REST (JSON); OAuth 2.0 CC; Webhook push; mTLS | Outbound queries; inbound scores and webhooks | On-demand at onboarding; quarterly batch; real-time sanctions webhook | → Service: company name, reg number, jurisdiction, VAT/TIN. ← Service: credit score, insolvency %, sanctions flag, ESG tier |
| Regulatory / Customs Portal | HTTPS REST; SOAP/XML (legacy portals); mTLS; EORI auth | Bidirectional | Per cross-border PO at placement; at GRN for import clearance | → Portal: HS codes, declared value, EORI numbers, PO reference. ← Portal: customs entry ref, duty amount, clearance status, dual-use flags |
| Email / Notification Service | SMTP TLS (port 587); vendor REST API (SendGrid / AWS SES) | Outbound only | Event-driven on workflow state transition | → Service: recipient, template ID, merge vars (PO number, amount, deadline, action URL) |
| Document Management System | CMIS 1.1 AtomPub HTTPS; vendor REST API; mTLS upload channel | Bidirectional | On contract execution, GRN finalisation, invoice approval; on-demand retrieval | → DMS: document binary (PDF/A-3), type, SCMP reference, metadata tags. ← DMS: document ID, version, SHA-256 hash, retrieval URL |
| Identity Provider (SSO) | SAML 2.0 HTTP POST; OIDC Authorization Code + PKCE; JWK-set; SCIM 2.0 | Inbound: assertions and provisioning events | Per session login; token refresh every 60 min; SCIM on HR change; SLO on logout | ← IdP: SAML Assertion / OIDC ID Token with sub, email, department, cost_centre, approval_limit_band, role_groups |

---

## Data Classification by Context

| Data Category | Flow Direction | Classification | Regulatory Frameworks | Representative Fields |
|---|---|---|---|---|
| Supplier legal entity master | Inbound from onboarding; shared with ERP | Confidential — PII | GDPR Art. 6(1)(b); UK GDPR; local data-protection law | Company name, VAT/TIN, registered address, contact name, work email, phone, IBAN |
| Supplier credit and risk scores | Inbound from risk service | Confidential — Financial / Regulatory | SOC 2 CC6; GDPR Art. 6(1)(f) if sole-trader PII involved | Credit score, insolvency probability, OFAC/EU/UN sanctions flag, ESG tier, adverse-media summary |
| Purchase order commercial data | Internal; outbound to supplier via EDI or portal | Confidential — Commercial | EAR/ECCN for dual-use goods; ITAR for defence items | Item description, HS/ECCN code, unit price, quantity, delivery address, Incoterms |
| Invoice financial data | Inbound from supplier; outbound to ERP | Confidential — Financial | EU VAT Directive 2006/112/EC; PEPPOL; Italy SDI; Mexico CFDI; Germany XRechnung; SOX §404 | Invoice number, gross/net amounts, VAT/GST breakdowns, line items, payment-due date |
| Payment instruction data | Outbound to bank gateway | Restricted — Financial | PSD2 SCA; SWIFT CSP; Dodd-Frank § 1073 | Beneficiary name, IBAN, BIC, currency, net amount, value date, remittance reference |
| User identity and entitlement data | Inbound from IdP; internal for authorisation | Confidential — PII | GDPR Art. 6(1)(b); ISO 27001 A.9 | Full name, corporate email, employee ID, department, cost-centre code, role assignments |
| Contract terms and pricing | Internal; archived to DMS | Restricted — Legal / Commercial | Attorney–client privilege; trade-secret protection; TRIPS | Unit prices, rebate tiers, SLA penalties, exclusivity periods, change-control clauses |
| Goods receipt and quality data | Internal; GRN accrual posted to ERP | Internal — Operational | ISO 9001 §8.6; FDA 21 CFR Part 11; GMP records | Received quantities, lot numbers, batch numbers, inspection results, NCR IDs |
| Customs declaration data | Outbound to customs portal | Confidential — Regulatory | EAR; EU Customs Code (UCC); WCO SAFE Framework; AMLD | HS codes, declared FOB value, EORI numbers, country of origin, export-licence references |
| Audit trail and event logs | Internal; SIEM export | Restricted — Security | SOC 2 CC7; ISO 27001 A.12.4; 7-year financial-audit retention | Timestamp, user sub, source IP, action type, entity ID, before/after field values |

---

## Security and Trust Boundaries

### Trust Zone Architecture

The SCMP operates across three discrete trust zones enforced at both the network perimeter and
the application authorisation layer. Zone boundaries are implemented through stateful
next-generation firewalls, application-layer reverse proxies, a Web Application Firewall (WAF),
and attribute-based access control policies evaluated at the API gateway on every inbound
request.

### Zone 1 — Internal Corporate Network (Elevated Trust)

Internal users access the SCMP exclusively from the corporate intranet or through a
corporate-managed VPN endpoint that enforces device health attestation:

- Managed device certificate verified
- Up-to-date EDR (Endpoint Detection & Response) agent confirmed
- OS patch compliance checked before VPN tunnel is established

**TLS and transport security:**
Traffic arrives at a Layer 7 Application Load Balancer that terminates TLS 1.3 (minimum cipher
suite TLS_AES_256_GCM_SHA384), enforces HTTP Strict Transport Security (HSTS) with a two-year
max-age and preload flag, and applies Content-Security-Policy headers to prevent XSS escalation.

**Authentication and token issuance:**
Authentication is delegated to the corporate Identity Provider via SAML 2.0 SP-initiated SSO.
Upon successful authentication, the SCMP's authorisation server issues:
- Short-lived JWT access tokens (60-minute TTL, signed RS256 with RSA-4096 key in a
  FIPS 140-2 Level 3 HSM)
- Rotating opaque refresh tokens (8-hour TTL, stored as hashed values in the token store)

Claims in the JWT — including `approval_limit_band`, `department`, `cost_centre`, and
`role_groups` — are sourced from the IdP's SAML attribute assertions and drive all
feature-level authorisation decisions within the application.

**Step-up MFA for high-risk operations:**
Privilege escalation for sensitive operations — approving payment batches above the CFO
threshold, modifying user role assignments, or resetting integration API credentials —
requires step-up MFA enforced at the IdP using either a TOTP authenticator or a FIDO2
hardware security key (WebAuthn). This ensures a compromised primary SSO session cannot
unilaterally authorise financial disbursements.

### Zone 2 — Supplier Self-Service Portal (Reduced Trust / Internet-Facing DMZ)

Supplier Representatives access a purpose-built portal on a dedicated subdomain
(`supplier.scmp.company.com`), hosted in a DMZ segment isolated from the internal
application tier by a stateful firewall with a default-deny policy.

**WAF and rate-limiting:**
All traffic traverses a WAF configured with:
- OWASP Core Rule Set v3.3 with tuned exclusions for false-positive reduction
- Custom rules for supplier-portal attack surface (file-upload abuse, bid-manipulation,
  SSRF attempts)
- Rate-limiting at 100 requests per minute per IP with graduated throttling
- Bot-mitigation via JavaScript challenge for anomalous request patterns

**Row-level security:**
The portal frontend communicates exclusively with a Backend-for-Frontend (BFF) API that
includes the supplier's organisation ID as a mandatory filter predicate on every downstream
database query. This prevents horizontal privilege escalation between supplier tenants
regardless of application-layer bugs.

**File upload safety:**
Supplier-uploaded documents pass through a sandboxed file-inspection service for:
- Malware scanning (ClamAV + cloud sandbox)
- Content-type validation (MIME sniffing against file header magic bytes)
- Maximum file-size enforcement (25 MB per document)

### Zone 3 — System Integration Hub (Controlled / Integration DMZ)

All machine-to-machine integrations operate through an API gateway and message broker
deployed in a dedicated integration DMZ, isolated from both Zone 1 and Zone 2.

**Mutual TLS (mTLS):**
All outbound calls to ERP REST APIs, the risk-scoring service, and the customs portal use
client certificates issued by the corporate PKI. Certificate rotation is automated via
the ACME protocol with 90-day validity periods.

**Secrets management:**
OAuth 2.0 client credentials, SFTP private keys (ED25519), PGP private keys for payment-file
encryption, and SMTP relay credentials are stored in HashiCorp Vault. All Vault secret
accesses are logged and trigger anomaly-detection alerts if accessed outside scheduled
integration-job execution windows.

**EDI non-repudiation:**
AS2 transmissions use S/MIME signing (SHA-256, RSA-2048) and require synchronous MDN receipts
within 60 seconds. Failed MDN receipts trigger automatic retry with exponential backoff
(30 s → 60 s → 120 s) and alert the integration operations team after three failures.

**Payment file integrity:**
Banking payment files are PGP-encrypted with the bank's pinned public key (RSA-4096)
before SFTP upload. A HMAC-SHA256 file-level checksum is submitted out-of-band via a
separate authenticated API call. The bank validates both before processing. All payment
API calls include a UUID v4 idempotency key to prevent duplicate execution on retries.

**ERP least privilege:**
The ERP integration service account has read-only SELECT access to GL master data, cost-
centre, and budget tables. Write access is scoped to exactly two function modules:
- `MIGO_GR_POST` — goods receipt accrual journal posting
- `MIRO_INV_POST` — invoice verification and payment journal posting

Direct access to vendor master write functions (`XK01/XK02`) and payment-programme
configuration is explicitly denied.

**Monitoring and audit:**
All integration-zone traffic is shipped to a centralised SIEM (Splunk / Microsoft Sentinel)
with 13-month hot-storage retention and 7-year cold archival. Correlation rules alert on:

- Out-of-hours payment-file submissions (outside 07:00–17:00 local business hours)
- Payment amounts exceeding the statistical 3-sigma daily average
- EDI volume spikes beyond 3× the 30-day rolling average
- Risk-scoring API error rates above 5% over a 15-minute window
- New secrets-access events outside scheduled integration job windows

The integration network is monitored by a passive IDS (Zeek) capturing full flow metadata
for retrospective investigation. Privileged access to production infrastructure is gated
through a just-in-time PAM tool with full session recording and automatic termination after
2 hours. The platform undergoes annual black-box penetration testing by a CREST-certified
third party and continuous SAST/DAST scanning integrated into the CI/CD pipeline with
policy gates blocking deployment on any CVSS ≥ 7.0 finding.

---

## Related Architecture Documents

| Document | Description | Location |
|---|---|---|
| Container Diagram | C4 Level 2 decomposition of internal SCMP services and databases | `analysis/container-diagram.md` |
| Activity Diagrams | UML activity diagrams for P2P, Supplier Onboarding, Goods Receipt, RFQ, and Invoice flows | `analysis/activity-diagrams.md` |
| Swimlane Diagrams | Cross-functional swimlane diagrams for PO lifecycle, onboarding, three-way match, and RFQ award | `analysis/swimlane-diagrams.md` |
| Use Case Descriptions | Detailed use case specifications for all SCMP actors | `analysis/use-case-descriptions.md` |
| Data Model | Entity-relationship diagram and data dictionary | `analysis/data-model.md` |
| API Specification | OpenAPI 3.1 specification for all internal and external-facing SCMP APIs | `analysis/api-specification.md` |
| Security Architecture | Threat model, STRIDE analysis, and security control mapping | `analysis/security-architecture.md` |
