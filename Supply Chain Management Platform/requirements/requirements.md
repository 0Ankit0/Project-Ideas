# Requirements — Supply Chain Management Platform

## System Overview

The Supply Chain Management Platform (SCMP) is a cloud-native, multi-tenant B2B procurement platform that digitises and automates the procure-to-pay (P2P) and source-to-contract (S2C) cycles. It connects buying organisations with their supplier networks, enforces internal controls, and provides real-time visibility into spend, risk, and supplier performance.

The platform is composed of the following functional modules:
- **Supplier Lifecycle Management** — onboarding, qualification, performance scoring, off-boarding
- **Procurement (PR→PO)** — purchase requisitions, multi-level approvals, purchase order issuance
- **Goods Receipt & Quality** — goods receipt notes, quality inspections, discrepancy tracking
- **Accounts Payable** — invoice receipt, three-way matching, dispute management, payment scheduling
- **Sourcing** — RFQ, RFP, and reverse auction event management
- **Contract Management** — contract authoring, spend monitoring, renewal alerts
- **Demand Forecasting** — collaborative rolling forecasts with supplier confirmation
- **Analytics & Reporting** — spend analytics, OTD/quality KPIs, executive dashboards

---

## Stakeholders

| Stakeholder | Role | Primary Interests |
|---|---|---|
| Procurement Manager | Internal buyer, manages supplier relationships and PO lifecycle | Efficient PO creation, supplier compliance, spend visibility |
| Supplier | External vendor providing goods or services | Clear PO communication, timely payment, easy document submission |
| Finance Manager / CFO | Owns budget, approves high-value transactions, monitors cash flow | Budget adherence, accurate invoice matching, payment forecast |
| Warehouse Manager | Receives and inspects goods, records GRNs | Accurate receipt recording, quality inspection workflow, discrepancy alerts |
| Approver (L1 / L2) | Line manager or department head approving requisitions | Fast, mobile-friendly approval interface with full context |
| IT Administrator | Manages platform configuration, integrations, and user access | Reliable APIs, audit logs, SSO/RBAC configuration |
| Compliance Officer | Ensures regulatory and policy adherence | Supplier qualification status, audit trails, GDPR controls |
| Category Manager | Manages strategic sourcing for specific spend categories | RFQ/RFP tooling, contract compliance, benchmarking data |

---

## Functional Requirements

### FR-SUP: Supplier Management

| ID | Requirement | Priority |
|---|---|---|
| FR-SUP-01 | The system shall support a self-service supplier registration portal where prospective suppliers complete a structured onboarding form (company details, tax ID, bank details, certifications). | Must |
| FR-SUP-02 | The system shall enforce a qualification workflow (document upload → internal review → approval/rejection) with configurable stages per supplier category. | Must |
| FR-SUP-03 | The system shall maintain a supplier qualification expiry date; expired suppliers are automatically blocked from receiving new POs. | Must |
| FR-SUP-04 | The system shall support supplier segmentation by category (raw materials, services, logistics), tier (strategic, preferred, approved, restricted), and geography. | Must |
| FR-SUP-05 | The system shall allow procurement managers to maintain multiple contacts per supplier, each with a defined role (account manager, billing, logistics). | Must |
| FR-SUP-06 | The system shall provide a supplier self-service portal where suppliers can view open POs, submit invoices, upload compliance documents, and check payment status. | Must |
| FR-SUP-07 | The system shall store and version supplier bank account details, requiring re-approval after changes to prevent fraud. | Must |
| FR-SUP-08 | The system shall track all supplier document types (insurance certificate, ISO certification, financial statements) with expiry alerts sent 60, 30, and 7 days before expiry. | Must |
| FR-SUP-09 | The system shall maintain a full audit log of all changes to supplier master data, including who changed what and when. | Must |
| FR-SUP-10 | The system shall support supplier suspension and off-boarding workflows, preventing new POs while allowing existing POs to complete. | Must |
| FR-SUP-11 | The system shall support importing supplier data in bulk via CSV or API for initial migration. | Should |
| FR-SUP-12 | The system shall integrate with a third-party credit/risk scoring service to flag high-risk suppliers during onboarding and on a periodic re-assessment schedule. | Should |

---

### FR-PRQ: Purchase Requisitions

| ID | Requirement | Priority |
|---|---|---|
| FR-PRQ-01 | The system shall allow any authorised employee to create a purchase requisition (PR) for goods or services, selecting items from the item master catalogue or entering free-text requests. | Must |
| FR-PRQ-02 | The system shall perform a real-time budget check against the requester's cost centre at the time of PR submission, rejecting submissions that would exceed the available budget. | Must |
| FR-PRQ-03 | The system shall route PRs through a configurable multi-level approval chain based on amount thresholds, cost centre, and item category. | Must |
| FR-PRQ-04 | The system shall send email and in-app notifications to approvers when a PR is pending their action, with daily escalation reminders. | Must |
| FR-PRQ-05 | The system shall allow approvers to approve, reject, or return-for-revision PRs with mandatory comments on rejection or return. | Must |
| FR-PRQ-06 | The system shall support consolidating multiple approved PRs into a single Purchase Order when they share the same supplier and cost centre. | Must |
| FR-PRQ-07 | The system shall allow requesters to attach supporting documents (quotes, specifications, justifications) to a PR. | Must |
| FR-PRQ-08 | The system shall maintain a complete PR status history (draft, submitted, under-review, approved, rejected, converted-to-PO). | Must |
| FR-PRQ-09 | The system shall allow delegation of approval authority when an approver is on leave, with audit trail of delegated approvals. | Should |

---

### FR-PO: Purchase Orders

| ID | Requirement | Priority |
|---|---|---|
| FR-PO-01 | The system shall generate a unique PO number and issue a formal Purchase Order document (PDF) to the supplier via the supplier portal and email. | Must |
| FR-PO-02 | The system shall support line-item granularity on POs, each with item description, quantity, unit of measure, unit price, tax code, and delivery date. | Must |
| FR-PO-03 | The system shall enforce a change order control process: any modification to an issued PO (price, quantity, delivery date) creates a versioned change order requiring supplier acknowledgement. | Must |
| FR-PO-04 | The system shall track PO acknowledgement from suppliers; unacknowledged POs are flagged after a configurable number of days. | Must |
| FR-PO-05 | The system shall support multi-currency POs, converting values to the organisation's base currency using the exchange rate at the time of PO issuance. | Must |
| FR-PO-06 | The system shall support blanket purchase orders with a maximum commitment amount and periodic release orders drawn against the blanket. | Must |
| FR-PO-07 | The system shall allow partial deliveries against a PO line, tracking open, received, and invoiced quantities separately. | Must |
| FR-PO-08 | The system shall close a PO line automatically when the received quantity matches the ordered quantity (within a configurable tolerance). | Must |
| FR-PO-09 | The system shall support multi-entity purchasing, where a single platform instance supports multiple legal entities each with their own number sequences, approval rules, and currency. | Must |
| FR-PO-10 | The system shall provide an inbound shipment tracking module where suppliers submit Advance Shipment Notices (ASNs) that are linked to open PO lines. | Must |
| FR-PO-11 | The system shall allow PO cancellation with mandatory reason codes, notifying the supplier and releasing the budget commitment. | Must |
| FR-PO-12 | The system shall support drop-ship POs where goods are delivered directly from supplier to end customer, updating the fulfilment record accordingly. | Should |

---

### FR-GR: Goods Receipt

| ID | Requirement | Priority |
|---|---|---|
| FR-GR-01 | The system shall allow warehouse staff to record a Goods Receipt Note (GRN) against an open PO, specifying actual quantities received per line. | Must |
| FR-GR-02 | The system shall support quality inspection at the point of receipt, allowing inspectors to accept, conditionally accept, or reject items with defect reason codes. | Must |
| FR-GR-03 | The system shall record lot/batch numbers, serial numbers, and expiry dates for applicable items during goods receipt. | Must |
| FR-GR-04 | The system shall generate a discrepancy report when received quantities differ from PO quantities or when items fail quality inspection. | Must |
| FR-GR-05 | The system shall trigger a Return-to-Vendor (RTV) workflow for rejected items, generating a debit note and updating the supplier performance record. | Must |
| FR-GR-06 | The system shall update inventory quantities in real time upon GRN confirmation. | Must |
| FR-GR-07 | The system shall notify the procurement manager and supplier when a GRN discrepancy exceeds a configurable threshold. | Must |
| FR-GR-08 | The system shall link ASN data to the GRN for tracking carrier, tracking number, and estimated delivery date. | Must |
| FR-GR-09 | The system shall support configurable quality inspection sampling rates (e.g., 100% inspection, AQL-based spot checks) by item category. | Should |

---

### FR-INV: Invoice & Payment

| ID | Requirement | Priority |
|---|---|---|
| FR-INV-01 | The system shall accept supplier invoices submitted via the supplier portal (manual entry), EDI, or email-to-OCR pipeline. | Must |
| FR-INV-02 | The system shall perform automated three-way matching: Invoice ↔ Purchase Order ↔ Goods Receipt, flagging variances outside the defined tolerance bands. | Must |
| FR-INV-03 | The system shall auto-approve invoices that pass three-way matching within tolerance and route exceptions to the AP team for manual review. | Must |
| FR-INV-04 | The system shall support a structured dispute workflow: AP clerk raises a dispute, the supplier responds, and the dispute is resolved (accepted/rejected) before payment is released. | Must |
| FR-INV-05 | The system shall calculate payment due dates based on supplier-specific payment terms (Net 30, 2/10 Net 30, etc.) stored on the supplier master. | Must |
| FR-INV-06 | The system shall generate a payment run file (BACSv2, ACH, SWIFT MT103) for integration with the corporate banking system. | Must |
| FR-INV-07 | The system shall support early payment discount capture, notifying the finance team when a discount window is open. | Should |
| FR-INV-08 | The system shall maintain a full audit trail of all invoice status transitions and matching decisions. | Must |
| FR-INV-09 | The system shall produce a cash flow forecast based on scheduled payment dates. | Should |

---

### FR-SRC: Sourcing

| ID | Requirement | Priority |
|---|---|---|
| FR-SRC-01 | The system shall allow category managers to create and publish RFQ (Request for Quotation) and RFP (Request for Proposal) events to selected suppliers. | Must |
| FR-SRC-02 | The system shall support a reverse auction engine where suppliers submit competitive bids within a defined time window, with real-time rank visibility to buyers. | Must |
| FR-SRC-03 | The system shall enforce a minimum number of invited suppliers per RFQ/RFP event (default: 3) to ensure competitive sourcing. | Must |
| FR-SRC-04 | The system shall support automated award recommendation based on configurable weighted scoring (price, quality score, OTD, lead time, sustainability). | Should |
| FR-SRC-05 | The system shall allow the creation of a PO or contract directly from an awarded RFQ/RFP, pre-populating agreed terms. | Must |
| FR-SRC-06 | The system shall maintain a full history of all sourcing events, bids, and award decisions for audit purposes. | Must |

---

### FR-CTR: Contract Management

| ID | Requirement | Priority |
|---|---|---|
| FR-CTR-01 | The system shall allow the creation of supplier contracts with key fields: effective date, expiry date, payment terms, agreed price list, and penalty clauses. | Must |
| FR-CTR-02 | The system shall alert contract owners 90, 60, and 30 days before contract expiry for renewal decisions. | Must |
| FR-CTR-03 | The system shall track actual spend against contracted spend commitments, flagging under-utilisation and over-spend. | Must |
| FR-CTR-04 | The system shall support electronic signature integration for contract execution (DocuSign or equivalent). | Should |
| FR-CTR-05 | The system shall version contracts, retaining all historical versions with change history and approver signatures. | Must |
| FR-CTR-06 | The system shall associate POs and invoices to the governing contract, enabling contract compliance reporting. | Must |

---

### FR-FOR: Forecasting

| ID | Requirement | Priority |
|---|---|---|
| FR-FOR-01 | The system shall support collaborative demand forecasting where buyers publish rolling 12-month quantity forecasts by item and supplier. | Must |
| FR-FOR-02 | The system shall allow suppliers to confirm, adjust, or flag exceptions to buyer-submitted forecasts via the supplier portal. | Must |
| FR-FOR-03 | The system shall highlight forecast-vs-actual variance by item and period, triggering alerts when variance exceeds 20%. | Must |
| FR-FOR-04 | The system shall generate suggested replenishment signals based on confirmed forecasts, current inventory levels, and supplier lead times. | Should |

---

### FR-ANA: Analytics & Reporting

| ID | Requirement | Priority |
|---|---|---|
| FR-ANA-01 | The system shall provide a real-time spend analytics dashboard showing spend by category, supplier, entity, and period with drill-down capability. | Must |
| FR-ANA-02 | The system shall calculate and display supplier KPIs including On-Time Delivery (OTD), quality acceptance rate, invoice accuracy rate, and response time. | Must |
| FR-ANA-03 | The system shall produce a procurement cycle time report showing average time from PR creation to PO issuance and from PO issuance to goods receipt. | Must |
| FR-ANA-04 | The system shall generate a supplier performance scorecard on a monthly or quarterly schedule, distributed automatically to supplier account managers. | Must |
| FR-ANA-05 | The system shall support ad-hoc report generation with configurable filters and CSV/Excel export. | Must |
| FR-ANA-06 | The system shall provide an executive dashboard with key metrics: total PO value, savings achieved, contract compliance %, active suppliers, and pending invoices. | Must |

---

## Non-Functional Requirements

### Performance

| ID | Requirement |
|---|---|
| NFR-PERF-01 | API response time for 95th percentile of read operations must be ≤ 300 ms under normal load. |
| NFR-PERF-02 | The three-way matching engine must process a batch of 10,000 invoices within 5 minutes. |
| NFR-PERF-03 | The platform must support 500 concurrent active users without degradation. |
| NFR-PERF-04 | Report generation for up to 12 months of spend data must complete within 30 seconds. |

### Availability

| ID | Requirement |
|---|---|
| NFR-AVA-01 | The platform must achieve 99.9% uptime (≤ 8.7 hours downtime per year) for the procurement core modules. |
| NFR-AVA-02 | Planned maintenance windows must be scheduled outside business hours and announced 48 hours in advance. |
| NFR-AVA-03 | The supplier portal must achieve 99.5% uptime to not block supplier invoice submission. |

### Security

| ID | Requirement |
|---|---|
| NFR-SEC-01 | All data in transit must be encrypted using TLS 1.3 or higher. |
| NFR-SEC-02 | All data at rest must be encrypted using AES-256. |
| NFR-SEC-03 | The platform must support SSO via SAML 2.0 and OAuth 2.0 / OIDC. |
| NFR-SEC-04 | Role-based access control (RBAC) must be enforced at the API level; privilege escalation must be prevented. |
| NFR-SEC-05 | All user actions on financial data must be logged in a tamper-evident audit log retained for 7 years. |
| NFR-SEC-06 | Bank account details must be masked in all UI views except for authorised finance roles. |
| NFR-SEC-07 | Supplier bank account changes must trigger a dual-approval workflow before activation. |

### Scalability

| ID | Requirement |
|---|---|
| NFR-SCA-01 | The architecture must support horizontal scaling of stateless API services. |
| NFR-SCA-02 | The platform must support up to 10,000 active suppliers and 1,000,000 POs per year. |
| NFR-SCA-03 | Database partitioning or archiving strategies must be implemented for tables exceeding 50 million rows. |

---

## Integration Requirements

| Integration | Direction | Protocol | Notes |
|---|---|---|---|
| ERP System (SAP S/4HANA, Oracle Fusion) | Bidirectional | REST API / iDocs | Sync item master, cost centres, GL codes, and payment confirmations |
| Corporate Banking (BACSv2, ACH, SWIFT) | Outbound | SFTP + BACSv2/MT103 | Payment file generation and status reconciliation |
| Shipping Carriers (FedEx, UPS, DHL) | Inbound | REST API | ASN tracking updates and proof-of-delivery confirmation |
| Email Service (SendGrid / SES) | Outbound | REST API | Notifications, approval requests, supplier alerts |
| SMS/WhatsApp (Twilio) | Outbound | REST API | Critical approval escalations and payment confirmations |
| eSignature (DocuSign / Adobe Sign) | Bidirectional | REST API | Contract execution and audit trail |
| Credit/Risk Scoring (Dun & Bradstreet, CreditSafe) | Inbound | REST API | Supplier risk assessment during onboarding and re-assessment |
| Customs / Trade Compliance (Descartes, Oracle GTM) | Inbound | REST API | Import/export compliance checks on POs for restricted items |
| HMRC / Tax Authority | Outbound | REST API | e-Invoicing and VAT reporting (Making Tax Digital) |

---

## Constraints

1. The platform must comply with GDPR for EU supplier personal data, including the right to erasure for supplier contacts.
2. Financial data must comply with SOX controls where the buying organisation is publicly listed.
3. The platform must support multi-language UI (English, French, German, Spanish) for the supplier portal.
4. All monetary values must be stored with 4 decimal places to avoid rounding errors in multi-currency scenarios.
5. The platform must be cloud-agnostic, deployable on AWS, Azure, or GCP.

## Assumptions

1. Each buying organisation configures its own approval thresholds and cost centre hierarchy during onboarding.
2. The ERP system is the system of record for item master and GL account data; SCMP syncs from ERP, not vice versa for these entities.
3. Supplier credit/risk scoring is advisory only and does not automatically block supplier registration.
4. Currency exchange rates are fetched daily from a configured FX provider and stored; historical rates are used for PO valuation at time of issuance.
5. The platform does not replace the ERP's inventory management system; it provides receipt data that the ERP consumes.
