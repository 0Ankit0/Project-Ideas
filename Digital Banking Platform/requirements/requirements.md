# Requirements Specification — Digital Banking Platform

**Document ID:** DBP-REQ-001  
**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-15  
**Owner:** Product Management  
**Reviewers:** Architecture, Compliance, Risk, Legal

---

## Introduction

### Purpose

This document defines the complete set of functional and non-functional requirements for the Digital Banking Platform (DBP). It serves as the authoritative contract between business stakeholders, product management, engineering, and compliance teams. All design decisions, implementation choices, and acceptance criteria must be traceable back to requirements defined here.

### Scope

The Digital Banking Platform covers the full lifecycle of a retail digital banking customer: identity verification and onboarding, account management, card issuance and controls, domestic and international money transfers, personal lending, real-time fraud detection, and regulatory reporting. The platform is intended to support up to 5 million retail customers at launch, scaling to 20 million over a 3-year horizon.

### Audience

- **Product Management** — requirements ownership and prioritisation
- **Engineering** — implementation guidance and acceptance criteria
- **Architecture** — system design and technology selection
- **Compliance & Legal** — regulatory requirement traceability
- **QA & Testing** — test case derivation
- **External Auditors** — evidence of regulatory control documentation

### Document Conventions

- Requirements prefixed `FR-` are functional requirements
- Requirements prefixed `NFR-` are non-functional requirements
- Priority levels: **P0** (must have at launch), **P1** (should have in v1.1), **P2** (nice to have)
- Each requirement has a unique ID that must be referenced in all related design documents, test cases, and implementation tickets

---

## Stakeholders

| Role | Organisation / Group | Primary Interest | Key Concerns |
|------|---------------------|-----------------|--------------|
| **Retail Customer** | End user (consumer) | Easy, fast, transparent banking experience on mobile and web | Data privacy, security of funds, low fees, 24/7 availability, responsive customer support |
| **Bank Admin** | Internal operations team | Efficient back-office tooling to manage customer accounts, process exceptions, and handle escalations | Audit trails, bulk operation support, permission granularity, clear workflow for regulatory cases |
| **Compliance Officer** | Risk & Compliance department | Ensure the platform meets all applicable AML, KYC, and data protection regulations | PEP/sanctions coverage, suspicious activity reporting (SAR), GDPR data mapping, regulatory change management |
| **Risk Manager** | Credit & Operational Risk | Control credit exposure and operational risk across lending, payments, and fraud | Credit scoring accuracy, fraud loss rates, concentration risk, real-time risk monitoring dashboards |
| **IT Operations** | Infrastructure / SRE team | Maintain platform reliability, deploy safely, respond to incidents | Observability coverage, deployment automation, incident runbooks, DR test evidence, on-call burden |
| **External Auditor** | Big-4 / Regulatory auditor | Verify controls are in place and operating effectively | Immutable audit logs, change management evidence, penetration test reports, access control reviews |
| **Card Network** (Visa / Mastercard) | Payment network | Correct implementation of network rules, certification compliance, and brand standards | EMV compliance, 3DS2 implementation, dispute resolution SLA, BIN management, chargeback rates |
| **Regulatory Body** (FCA / OCC / ECB) | Financial regulator | Protect consumer interests, maintain financial stability, ensure orderly markets | Capital adequacy, safeguarding of customer funds, operational resilience (PS21/3), open banking compliance (PSD2), AML programme effectiveness |
| **Open Banking TPP** | Third-party payment initiation / account information service providers | Secure, standards-compliant API access to customer account data and payment initiation | OAuth2 PKCE consent flows, PSD2 SCA compliance, API availability SLA, developer onboarding experience |

---

## Functional Requirements

### Account Management

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-ACC-001** | The system shall allow prospective customers to open a new current account entirely via digital channels (web or mobile app) without requiring a branch visit | P0 | Subject to successful KYC completion per FR-KYC-001 through FR-KYC-006 |
| **FR-ACC-002** | The system shall enforce a KYC gate: no account shall become operational (able to send/receive funds) until the KYC workflow has reached `APPROVED` status | P0 | Accounts in `PENDING_KYC` state may only receive a welcome credit from the bank |
| **FR-ACC-003** | The system shall support multi-currency sub-accounts (currency pockets) within a single customer account, with individual balances, IBANs (where applicable), and account numbers for at least 30 supported currencies | P0 | Currency list configurable via reference data service; FX rates via FR-TXN-009 |
| **FR-ACC-004** | The system shall provide real-time balance inquiry for all currency pockets, with a response time compliant with NFR-PERF-001 | P0 | Balance must reflect reserved funds for pending authorisations |
| **FR-ACC-005** | The system shall generate monthly account statements in PDF and CSV format containing all debits, credits, opening balance, closing balance, and running balance per transaction | P0 | Statements must be retained for 7 years per NFR-COMP-003 |
| **FR-ACC-006** | The system shall support account closure requested by the customer, subject to: zero balance across all pockets, no pending loans, no active standing orders, and a 30-day cooling-off period | P0 | Closure initiates GDPR data minimisation review |
| **FR-ACC-007** | The system shall allow the customer or bank admin to set an overdraft limit (£0 – £5,000) on GBP current accounts; overdraft usage shall accrue interest daily at the configured overdraft rate | P1 | Overdraft eligibility subject to credit assessment |
| **FR-ACC-008** | The system shall detect account dormancy after 12 consecutive months of no customer-initiated transactions and transition the account to `DORMANT` status, restricting outbound transfers until the customer re-activates via identity-verified channel | P1 | Dormancy notification at T-30 and T-7 days |
| **FR-ACC-009** | The system shall allow customers to add, edit, and remove external payment beneficiaries; a first-payment confirmation delay of 24 hours shall apply to new beneficiaries unless the customer completes an additional verification step (OTP + biometric) | P0 | Beneficiary list stored per customer; shared across transfer types |
| **FR-ACC-010** | The system shall support joint accounts with up to 3 named account holders; any one account holder shall be able to initiate transactions below a configurable threshold; above the threshold, all joint holders must approve | P1 | Joint account KYC required for all holders |

---

### Card Management

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-CARD-001** | The system shall issue a virtual Visa or Mastercard debit card instantly upon account activation; the card shall be available for use in Apple Pay, Google Pay, and Samsung Pay immediately via push provisioning (MDES/VTS tokenisation) | P0 | Card details (PAN, expiry, CVV) displayed in-app with field-level encryption |
| **FR-CARD-002** | The system shall allow customers to request a physical personalised card (name embossing, chip + contactless); physical card shall be dispatched within 1 business day and delivered within 3–5 business days domestically | P0 | Physical card production integrates with card bureau (Thales/Giesecke) |
| **FR-CARD-003** | The system shall allow customers to freeze and unfreeze their card in real time (< 2 seconds propagation to card authorisation system) via the mobile app or web portal | P0 | Frozen card returns decline code `57` on all authorisations |
| **FR-CARD-004** | The system shall support customer-initiated PIN management: set PIN (post-issuance), change PIN, and forgotten PIN reset via secure in-app flow without requiring call centre contact | P0 | PIN stored as a one-way hash in HSM; PIN operations use HSM key blocks |
| **FR-CARD-005** | The system shall allow customers to configure per-category spending limits (e.g., gambling max £50/day, online retail max £1,000/day, ATM withdrawal max £500/day) enforced at authorisation time | P1 | Categories based on MCC code mapping |
| **FR-CARD-006** | The system shall implement 3-D Secure 2.2 (3DS2) for all card-not-present transactions; frictionless flow shall be attempted first; step-up (OTP / biometric) triggered based on risk score from fraud service | P0 | PCI 3DS requirement; must pass Visa/Mastercard certification |
| **FR-CARD-007** | The system shall support card replacement for lost, stolen, or damaged cards; the old card shall be cancelled immediately upon replacement request; a new card (virtual and/or physical) shall be issued within 60 seconds (virtual) or 5 business days (physical) | P0 | PAN changes on replacement; new token provisioning required |
| **FR-CARD-008** | The system shall provide a self-service transaction dispute flow: customer raises dispute, system initiates chargeback via card network API (Visa Dispute Resolution / Mastercard Dispute Resolution), tracks status, and notifies customer at each stage change | P0 | Chargeback deadlines: 120 days from transaction date (Visa), 120 days (MC) |

---

### Money Transfer

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-TXN-001** | The system shall support outbound domestic bank transfers (sort code + account number for GBP, routing number + account number for USD) via Faster Payments and ACH respectively, with funds reaching the beneficiary within the network's published settlement window | P0 | Faster Payments: within 2 hours (typically < 20 seconds); ACH same-day: by 5pm ET |
| **FR-TXN-002** | The system shall support ACH batch origination (CCD, PPD, WEB entry classes) compliant with NACHA Operating Rules, including pre-notification (prenote), return processing (R-codes), and NOC (notification of change) handling | P0 | Batch files submitted via Moov ACH gateway |
| **FR-TXN-003** | The system shall support outbound SWIFT international wire transfers using ISO 20022 pacs.008 messages, with support for SHA, OUR, and BEN charge options; SWIFT GPI must be enabled for real-time payment status tracking | P0 | SWIFT connectivity via Finastra Universal Payments Hub |
| **FR-TXN-004** | The system shall support SEPA Credit Transfer (SCT) for same-day EUR payments within the SEPA zone; SEPA Instant Credit Transfer (SCT Inst) for EUR payments settled within 10 seconds; SEPA Direct Debit (SDD Core) for recurring collections | P0 | EPC rulebook compliance; IBAN validation required |
| **FR-TXN-005** | The system shall support internal transfers between accounts held within the platform; internal transfers shall settle immediately via atomic ledger double-entry with no external network dependency | P0 | T+0 settlement; idempotency key required per transfer |
| **FR-TXN-006** | The system shall allow customers to schedule future-dated transfers (up to 365 days in advance); the scheduler shall initiate the transfer on the target date if sufficient funds exist; if funds are insufficient, the customer shall be notified and given 2 hours to top up before the transfer is cancelled | P0 | Scheduler uses cron-based job with idempotency guard |
| **FR-TXN-007** | The system shall support recurring transfers (standing orders): daily, weekly, fortnightly, monthly, quarterly, annually; customers can configure start date, end date or number of occurrences, and first/last payment handling | P0 | Standing orders subject to same beneficiary delay rules as FR-ACC-009 |
| **FR-TXN-008** | The system shall provide a beneficiary management capability allowing customers to save, name, and organise external payees; validated beneficiary details (name, account number) must be confirmed via Confirmation of Payee (CoP) API before first payment | P0 | CoP API integration with Pay.UK open banking directory |
| **FR-TXN-009** | The system shall support real-time FX conversion for cross-currency payments; customers shall be presented with a firm indicative rate valid for 30 seconds; upon confirmation within the validity window, the rate shall be locked and the transfer executed | P0 | FX rates from Refinitiv feed; spread configured per currency pair |
| **FR-TXN-010** | The system shall support transfer reversal/recall within 24 hours for internal transfers and within network-permitted windows for ACH (R05 reversal file) and SWIFT (gSRP recall message); reversal availability and status must be surfaced in the customer app | P1 | Reversal eligibility rules per network; no reversal guarantee for SEPA Instant |

---

### KYC & Onboarding

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-KYC-001** | The system shall accept digital uploads of government-issued identity documents (passport, national identity card, driver's licence) in JPEG, PNG, or PDF format; documents up to 10 MB shall be supported | P0 | Documents encrypted at rest; stored in S3 with access logging |
| **FR-KYC-002** | The system shall perform automated OCR extraction of identity data (name, date of birth, document number, nationality, expiry date) from uploaded documents using a third-party provider (Onfido); extracted data shall be returned within 30 seconds | P0 | Fallback to manual review queue if OCR confidence < 80% |
| **FR-KYC-003** | The system shall conduct a biometric liveness check by prompting the customer to perform random face movements in front of the front-facing camera; liveness score must exceed 0.85 threshold to pass | P0 | Anti-spoofing: rejects photos, videos, and masks |
| **FR-KYC-004** | The system shall cross-reference extracted identity data against credit reference agency databases (Experian, Equifax) to confirm identity existence and address history; a minimum of two independent data sources must confirm identity | P0 | Uses Experian CrossCore orchestration; result stored in KYC record |
| **FR-KYC-005** | The system shall screen every customer in real time against PEP (Politically Exposed Persons) and global sanctions lists including OFAC SDN, UN Consolidated, EU Consolidated, HM Treasury, and AUSTRAC; screening must complete within 10 seconds | P0 | Provider: Dow Jones Risk & Compliance; continuous screening enabled |
| **FR-KYC-006** | The system shall assign a risk tier (`STANDARD`, `ENHANCED`, `HIGH_RISK`) to each customer based on KYC outcomes, PEP/sanctions result, country of origin, source of funds, and transaction behaviour; risk tier drives ongoing monitoring frequency and transaction limits | P0 | Risk tier reassessment on trigger events |
| **FR-KYC-007** | The system shall trigger a re-KYC workflow when: document expiry is within 90 days, a risk-tier-upgrade event is detected, a suspicious activity flag is raised, or the periodic refresh schedule fires (annual for `HIGH_RISK`, triennial for `STANDARD`) | P0 | Re-KYC notification sent 90 days, 30 days, and 7 days in advance |
| **FR-KYC-008** | The system shall initiate an Enhanced Due Diligence (EDD) workflow for `HIGH_RISK` customers requiring: source-of-funds declaration, source-of-wealth documentation, senior management sign-off, and enhanced ongoing transaction monitoring with alert thresholds set 50% below standard | P0 | EDD case managed in back-office AML system |

---

### Loan Management

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-LOAN-001** | The system shall provide a digital personal loan application for eligible customers (must have active account in good standing for ≥ 90 days); application shall capture: loan amount (£500–£50,000), purpose, requested tenure (6–84 months) | P0 | Pre-fill application from known customer data |
| **FR-LOAN-002** | The system shall initiate an automated hard credit bureau pull from Experian and Equifax upon loan application submission; bureau report must be retrieved within 30 seconds; customer must have provided explicit consent (FCA COBS 4.2A) | P0 | Hard search recorded on customer credit file |
| **FR-LOAN-003** | The system shall compute a loan eligibility score using: bureau credit score, DBT (days beyond terms), existing debt obligations, income estimation from transaction history, employment status, and requested LTI (loan-to-income ratio); score must be calculated in < 5 seconds | P0 | In-house ML model + rules engine; explainability required for declined decisions |
| **FR-LOAN-004** | The system shall generate up to 3 personalised loan offer variants (varying amount, rate, and tenure) based on the eligibility score and current risk appetite configuration; offers shall be valid for 30 days and presented with APR, monthly repayment amount, total cost of credit, and representative example | P0 | FCA Consumer Credit Act disclosure requirements |
| **FR-LOAN-005** | The system shall disburse the approved loan amount to the customer's primary GBP account within 60 seconds of e-signature completion and final fraud check passing; disbursement via internal ledger transfer | P0 | Disbursement triggers repayment schedule creation |
| **FR-LOAN-006** | The system shall generate a repayment schedule with fixed monthly instalments (principal + interest); support early full repayment with no penalty; support partial prepayment (minimum £100) reducing tenure by default; support payment holiday (maximum 2 per year, maximum 3 consecutive months) subject to lender approval | P1 | Payment holidays accrue interest during deferral period |

---

### Notifications

| ID | Requirement | Priority | Notes |
|----|------------|---------|-------|
| **FR-NOTIF-001** | The system shall send real-time push notifications to the customer's registered mobile device(s) for: account credit, account debit, card authorisation, card decline, login from new device, password change, and KYC status change; delivery target: 95% within 5 seconds | P0 | APNs (iOS) and FCM (Android); tokens managed per-device |
| **FR-NOTIF-002** | The system shall send SMS notifications for: OTP/2FA codes, large transaction alerts (> £1,000), failed login attempts (3+), account block, and card block; SMS must be delivered via Twilio with fallback to a secondary provider (AWS SNS) | P0 | SMS must not contain account numbers or card PANs |
| **FR-NOTIF-003** | The system shall send transactional emails for: account opening confirmation, monthly statement ready, loan offer, loan disbursement, loan repayment due reminder (T-3 days), password reset, and data subject access request confirmation; email via SendGrid with DKIM/DMARC | P0 | HTML and plain-text versions required |
| **FR-NOTIF-004** | The system shall provide an in-app notification centre displaying all notification history for the past 90 days; notifications shall be paginated, filterable by type, and marked read/unread; deep links from notifications shall navigate to relevant app screens | P1 | In-app notifications stored in notification service database |
| **FR-NOTIF-005** | The system shall provide a webhook delivery mechanism for registered Open Banking TPP partners; webhooks shall be sent for: account credit/debit events, payment status changes, and card authorisation events; delivery with at-least-once semantics, HMAC-SHA256 payload signing, and automatic retry with exponential backoff (max 24 hours) | P0 | Webhook subscriptions managed via Developer Portal API |

---

## Non-Functional Requirements

### Availability

| ID | Requirement | Target | Measurement |
|----|------------|--------|------------|
| **NFR-AVAIL-001** | Core banking platform (account management, payment processing, card authorisation) shall achieve 99.99% availability | < 52.6 minutes unplanned downtime per year | Monthly uptime percentage, measured by external synthetic monitoring (Pingdom / Catchpoint) from 3 geographic locations |
| **NFR-AVAIL-002** | KYC onboarding and loan origination shall achieve 99.9% availability | < 8.7 hours downtime per year | Allowance for third-party provider degradation |
| **NFR-AVAIL-003** | Planned maintenance windows shall not exceed 4 hours per quarter, conducted between 01:00–05:00 UTC on Sundays | Max 16 hours/year planned | 72-hour advance notice to customers and TPPs required |
| **NFR-AVAIL-004** | No single point of failure shall exist in the critical payment path; all critical services shall be deployed with a minimum of 3 replicas across 2 availability zones | Measured by architecture review | Validated by quarterly chaos engineering exercises |

### Performance

| ID | Requirement | Target | Measurement |
|----|------------|--------|------------|
| **NFR-PERF-001** | REST API response time for account balance inquiry, transaction list, and card controls shall meet P95 < 50ms, P99 < 100ms under nominal load | P95 < 50ms, P99 < 100ms | Measured at API gateway layer; k6 performance test suite |
| **NFR-PERF-002** | Payment initiation (domestic transfer, internal transfer) shall complete end-to-end (API acceptance through ledger posting) within P99 < 5 seconds | P99 < 5s | End-to-end timing including fraud check |
| **NFR-PERF-003** | Card authorisation response (from network gateway receipt to authorisation decision returned) shall complete within P99 < 150ms | P99 < 150ms | Visa/Mastercard network SLA requires < 1 second; internal target tighter |
| **NFR-PERF-004** | KYC document verification end-to-end shall complete within P50 < 30 seconds, P95 < 120 seconds | P50 < 30s, P95 < 120s | Dependent on third-party OCR and liveness provider SLA |
| **NFR-PERF-005** | The platform shall support a peak sustained load of 10,000 payment transactions per second (TPS) across all payment types | 10,000 TPS | Load tested quarterly; Kafka partition count sized accordingly |

### Scalability

| ID | Requirement | Target |
|----|------------|--------|
| **NFR-SCALE-001** | The platform shall horizontally scale to support 1,000,000 concurrent authenticated sessions | KEDA-driven autoscaling based on Kafka consumer lag and CPU/memory metrics |
| **NFR-SCALE-002** | Individual microservices shall scale independently without requiring changes to other services | Achieved via Kubernetes HPA and KEDA; validated by load testing |
| **NFR-SCALE-003** | Database tier shall support read scaling via read replicas; write capacity shall be achievable through sharding by customer_id for Cassandra and connection pooling (PgBouncer) for PostgreSQL | Cassandra cluster sized for 50,000 writes/second |
| **NFR-SCALE-004** | The event backbone (Apache Kafka) shall be sized to handle 5× peak TPS (50,000 events/second) with 7-day retention at full throughput | MSK cluster provisioned with 12 broker nodes minimum |

### Security

| ID | Requirement | Target |
|----|------------|--------|
| **NFR-SEC-001** | All data in transit between clients and the platform shall use TLS 1.3; TLS 1.0 and 1.1 shall be explicitly disabled | Verified by Qualys SSL Labs A+ rating |
| **NFR-SEC-002** | All data at rest (databases, object storage, backups) shall be encrypted using AES-256-GCM with keys managed by AWS KMS (envelope encryption) | Annual key rotation; key usage logged to CloudTrail |
| **NFR-SEC-003** | All internal service-to-service communication shall use mTLS enforced by Istio service mesh; services shall not accept plain HTTP on the service mesh | mTLS enforced at sidecar level; no service-account bypass |
| **NFR-SEC-004** | The Cardholder Data Environment (CDE) shall be isolated in a dedicated network segment; PAN data shall only be stored in the PCI-scoped vault (HashiCorp Vault with KMIP); all other services shall use tokenised card references | Annual PCI-DSS Level 1 assessment by QSA |
| **NFR-SEC-005** | All secrets (database passwords, API keys, certificates) shall be stored in and fetched from HashiCorp Vault; no secrets shall appear in code, configuration files, or container images | Enforced via pre-commit hooks and CI scanning (detect-secrets) |
| **NFR-SEC-006** | The platform shall implement OAuth 2.0 with PKCE (RFC 7636) for all customer-facing authentication; OIDC (OpenID Connect) for SSO; session tokens shall expire after 15 minutes of inactivity with a maximum absolute lifetime of 8 hours | Keycloak as OIDC provider; token introspection at API gateway |
| **NFR-SEC-007** | Multi-factor authentication (MFA) shall be mandatory for all privileged operations (payments above £500, new beneficiary addition, password change, card unblock) and for all bank staff accessing back-office systems | TOTP (RFC 6238) and push biometric |
| **NFR-SEC-008** | The platform shall undergo annual penetration testing by a CREST-certified third party; critical findings must be remediated within 7 days, high findings within 30 days | Pentest scope: web, mobile, API, infrastructure, and social engineering |

### Compliance

| ID | Requirement | Regulation | Notes |
|----|------------|-----------|-------|
| **NFR-COMP-001** | The platform shall comply with PCI-DSS v4.0 Level 1 requirements for handling, processing, and storing cardholder data | PCI-DSS v4.0 | Assessed annually by QSA; quarterly network scans by ASV |
| **NFR-COMP-002** | The platform shall comply with GDPR (EU 2016/679) and UK GDPR; data subject rights (access, erasure, portability, rectification, restriction) shall be fulfillable within 30 days | GDPR / UK GDPR | DPA (Data Processing Agreements) with all sub-processors |
| **NFR-COMP-003** | Transaction records, audit logs, and account statements shall be retained for a minimum of 7 years from the date of transaction; records shall be immutable and stored in WORM (Write Once Read Many) compliant storage (S3 Object Lock) | BSA, FCA SYSC, CASS | Right-to-erasure applies only to non-financial PII |
| **NFR-COMP-004** | The platform shall implement an AML transaction monitoring programme compliant with the Bank Secrecy Act (BSA), EU 6AMLD, and the Proceeds of Crime Act 2002 (POCA); SAR filing capability must be integrated with FinCEN / NCA systems | BSA, EU 6AMLD, POCA | Automated alert generation; human review workflow |
| **NFR-COMP-005** | The platform shall implement PSD2 / Open Banking APIs compliant with the UK Open Banking Standard v3.1.11 and Berlin Group NextGenPSD2 v1.3; Strong Customer Authentication (SCA) shall be enforced for all payment initiation and account access | PSD2, UK Open Banking | Dedicated TPP sandbox environment required |
| **NFR-COMP-006** | OFAC, UN, and EU sanctions screening must occur on every customer onboarding event and on every payment instruction exceeding USD 3,000 equivalent; real-time screening results must be logged with provider response and match confidence score | OFAC regulations | Zero-tolerance policy for processing OFAC SDN matches |

### Resilience & Recovery

| ID | Requirement | Target |
|----|------------|--------|
| **NFR-RES-001** | Recovery Point Objective (RPO) for all transactional databases shall be ≤ 4 hours; no more than 4 hours of committed data shall be lost in the event of a catastrophic regional failure | Achieved via synchronous replication within AZ and asynchronous replication to DR region |
| **NFR-RES-002** | Recovery Time Objective (RTO) for the core payment and account management services shall be ≤ 1 hour from declaration of a regional disaster | Validated by quarterly DR runbook execution |
| **NFR-RES-003** | Individual service failures shall not cascade into platform-wide outages; circuit breakers (Resilience4j) shall be configured on all synchronous inter-service calls with timeout, retry, and fallback policies | Chaos engineering validation via LitmusChaos |
| **NFR-RES-004** | All database operations in the payment critical path shall be idempotent; duplicate requests identified by idempotency key shall return the original response without re-executing the operation | Idempotency keys stored in Redis with 24-hour TTL |

### Audit & Observability

| ID | Requirement | Target |
|----|------------|--------|
| **NFR-OBS-001** | Every state-changing operation (account creation, payment initiation, card action, KYC status change) shall produce an immutable audit log entry containing: actor identity, timestamp (UTC), operation type, before/after state, source IP, and correlation ID | Audit events published to dedicated append-only Kafka topic; archived to S3 Glacier |
| **NFR-OBS-002** | All services shall emit structured JSON logs (level, timestamp, service, correlation_id, message, context) to the centralised ELK stack; log retention shall be 90 days hot, 1 year warm, 7 years cold (Glacier) | Enforced via log shipping sidecar |
| **NFR-OBS-003** | All services shall emit Prometheus-compatible metrics; RED metrics (Rate, Errors, Duration) shall be instrumented for every public API endpoint and Kafka consumer | Grafana dashboards per service; PagerDuty on-call integration |
| **NFR-OBS-004** | Distributed tracing (OpenTelemetry + Jaeger) shall be instrumented across all service calls; trace sampling rate shall be 100% for error traces and 1% for success traces | Trace correlation IDs propagated via W3C TraceContext headers |

---

## Constraints

### Technical Constraints

- **TC-001** — The platform must be deployable on AWS; migration to a secondary cloud provider (Azure/GCP) must be architecturally possible within 12 months without re-writing core business logic
- **TC-002** — All microservices must be containerised (Docker) and deployable on Kubernetes; no platform-specific managed services that cannot be replaced with a self-hosted alternative may be used in the critical payment path
- **TC-003** — The card processing network integration (Visa DPS / Mastercard MDES) requires ISO 8583 message format support in the card authorisation path; the internal card service must translate ISO 8583 to/from internal domain events
- **TC-004** — SWIFT connectivity mandates use of a certified SWIFT Service Bureau or direct SWIFT connectivity partner; direct self-hosted SWIFT Alliance Gateway requires separate SWIFT certification (18–24 months lead time)

### Regulatory Constraints

- **RC-001** — The platform may not process payments involving OFAC SDN-listed entities under any circumstances; a real-time hard block must be implemented with no override capability short of formal OFAC licence
- **RC-002** — UK FCA Electronic Money Institution (EMI) authorisation requires segregation of customer funds from operational funds; customer funds must be held in a safeguarding account (CASS 7A)
- **RC-003** — All consumer credit products (personal loans) require FCA Consumer Credit Authorisation; the platform may not offer credit products in the UK without this authorisation being in place
- **RC-004** — GDPR prohibits transfer of EU personal data to non-adequate third countries without appropriate safeguards (SCCs/BCRs); all personal data processing for EU customers must be within the EU region

### Budget Constraints

- **BC-001** — Infrastructure cloud spend must not exceed USD 200,000/month in the first year; right-sizing reviews shall be conducted quarterly
- **BC-002** — Third-party SaaS costs (Onfido, Dow Jones, Marqeta) are capped at 15% of total operational costs; alternatives must be evaluated if costs exceed this threshold

### Timeline Constraints

- **TL-001** — MVP (P0 requirements) must be deliverable within 12 months of project kick-off
- **TL-002** — PCI-DSS Level 1 certification must be achieved before processing live cardholder data (typically 6–12 months engagement with QSA)

---

## Assumptions

- **A-001** — The platform will initially target UK and EU retail customers; US market expansion (OCC/FDIC regulatory requirements) is planned for Year 2
- **A-002** — Integration with Marqeta as the primary card issuing processor is agreed in principle; Marqeta sandbox environment is accessible during development
- **A-003** — The bank has (or will obtain) an FCA Electronic Money Institution licence before go-live; development may proceed in parallel with the authorisation process
- **A-004** — Credit bureau integration agreements with Experian and Equifax are in place; API credentials will be provisioned in the sandbox environment by Sprint 3
- **A-005** — Customer support (live chat, phone) is handled by a separate CRM system (e.g., Zendesk); this platform provides webhooks and an admin API for CRM integration but does not own the CRM
- **A-006** — The FX rate feed (Refinitiv) provides rates with < 1-second latency; cached rates used only during feed unavailability with a maximum staleness of 60 seconds
- **A-007** — Open Banking TPP registration is managed via the Open Banking Directory (UK) and EBA PISP/AISP register (EU); the platform trusts eIDAS certificates for EU TPP identification

---

## Out of Scope

The following items are explicitly outside the scope of this platform and requirements document. Separate product initiatives may address these in future phases.

| Item | Rationale |
|------|-----------|
| **Cryptocurrency trading or custody** | Requires separate regulatory authorisation (crypto asset business registration with FCA/FinCEN) and specialist infrastructure; separate product stream |
| **Mortgage origination or servicing** | Highly regulated (FCA Mortgage Conduct of Business, MCOB); requires separate system of record; significant integration with credit risk and property valuation systems |
| **Insurance products** | Requires FCA General Insurance Distribution authorisation; separate actuarial and policy administration system required |
| **B2B / SME payments** | SWIFT MT103/MT202, BACS Direct Debit, and CHAPS for corporate customers require separate onboarding, credit, and treasury management capabilities; targeted for Year 2 roadmap |
| **Trade finance** | Letters of credit, documentary collections, and trade guarantees are complex structured finance products outside retail banking scope |
| **Investment / brokerage services** | Requires FCA Investment Firm authorisation (MiFID II); separate custody and settlement infrastructure |
| **ATM network management** | Physical ATM deployment, maintenance, and network management are out of scope; the platform uses Mastercard/Visa ATM networks via card scheme membership |
| **Branch banking systems** | No branch teller, cash handling, or in-branch appointment system is in scope; this is a digital-first platform |

---

*End of Requirements Specification*  
*Document ID: DBP-REQ-001 | Version 1.0 | Classification: CONFIDENTIAL*
