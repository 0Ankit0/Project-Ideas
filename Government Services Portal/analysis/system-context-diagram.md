# System Context Diagram — Government Services Portal

## Overview

This document presents the C4 System Context diagram and supporting context views for the Government Services Portal, showing the portal's position within the broader ecosystem of government digital infrastructure, external services, and human actors.

---

## C4 Context Diagram

```mermaid
C4Context
    title System Context: Government Services Portal

    Person(citizen, "Citizen", "Registered individual accessing government services online via web or mobile browser")
    Person(fieldOfficer, "Field Officer", "Government employee reviewing and processing service applications")
    Person(deptHead, "Department Head", "Senior official managing department configuration, escalations, and performance")
    Person(superAdmin, "Super Admin", "Platform administrator managing departments, security, and integrations")
    Person(auditor, "Auditor", "Compliance officer with read-only audit and reporting access")

    System(portal, "Government Services Portal", "Central digital platform enabling citizens to discover, apply for, and track government services online. Includes citizen portal (Next.js), officer console (Django), API server (DRF), and workflow engine (Celery).")

    System_Ext(aadhaar, "NID / NASC (National Identity Management Centre)", "National biometric identity authority. Provides OTP-based authentication API and demographic data retrieval for citizen identity verification.")
    System_Ext(digilocker, "Nepal Document Wallet (NDW)", "Government document repository. Provides OAuth 2.0-based API for citizens to authorise access to their verified digital documents (driving licence, marksheets, ration card, etc.).")
    System_Ext(paygov, "ConnectIPS / Razorpay", "Government Payment Gateway (GePG). Processes online fee payments (eSewa/Khalti/ConnectIPS, net banking, debit/credit card) and provides webhook-based payment confirmation.")
    System_Ext(smsGateway, "SMS Gateway (Twilio / NIC)", "Telecom messaging gateway for transactional SMS delivery (OTP, ARN confirmation, status alerts, reminders).")
    System_Ext(emailSES, "Email Service (AWS SES)", "Transactional email delivery service for notifications, receipts, certificates, and reports.")
    System_Ext(nationalRegistry, "National Citizen Registry", "Federal government database providing demographic validation services (address verification, family record lookup).")
    System_Ext(legacySystems, "Department Legacy Systems", "Existing department-specific databases and management systems (land records, birth/death registry, pension systems). Portal integrates via batch file exchange or REST APIs where available.")

    Rel(citizen, portal, "Registers, submits applications, pays fees, tracks status, downloads certificates, files grievances", "HTTPS / Next.js UI")
    Rel(fieldOfficer, portal, "Reviews application queue, approves/rejects applications, requests info, generates reports", "HTTPS / Django Admin + Officer Console")
    Rel(deptHead, portal, "Configures services, manages officers, monitors performance, approves escalations", "HTTPS / Django Admin")
    Rel(superAdmin, portal, "Manages departments, platform configuration, security policies, integrations", "HTTPS / Django Admin")
    Rel(auditor, portal, "Reads audit trails, generates compliance reports, verifies certificates", "HTTPS / Auditor Dashboard")

    Rel(portal, aadhaar, "Citizen OTP request, OTP verification, demographic data fetch (on consent)", "HTTPS / NASC (National Identity Management Centre) OTP API v2")
    Rel(portal, digilocker, "OAuth 2.0 token exchange, document list fetch, document pull for verified documents", "HTTPS / Nepal Document Wallet (NDW) Gateway API v3")
    Rel(portal, paygov, "Create payment order, redirect citizen, receive webhook, query payment status", "HTTPS / GePG REST API + HMAC Webhooks")
    Rel(portal, smsGateway, "Send OTP SMS, transactional notifications, reminders, broadcast messages", "HTTPS / REST API")
    Rel(portal, emailSES, "Send confirmation emails, receipt PDFs, certificate links, report downloads", "HTTPS / AWS SES SMTP")
    Rel(portal, nationalRegistry, "Validate citizen address and demographic data on application submission", "HTTPS / National Registry API (read-only)")
    Rel(portal, legacySystems, "Fetch pre-existing citizen data (land records, pension status), push approved application results", "HTTPS REST / SFTP Batch")
```

---

## External System Integration Details

### NID / NASC (National Identity Management Centre)

| Attribute | Value |
|-----------|-------|
| **Integration Type** | REST API (NASC (National Identity Management Centre) OTP Service v2) |
| **Purpose** | Citizen identity verification during registration and login |
| **Data Exchanged** | NID number (one-way hash in requests), OTP, masked demographic data (name, gender, DoB) on consent |
| **Data Sensitivity** | Highly Sensitive PII — NID Act 2016 compliance mandatory |
| **Compliance** | NID Act 2016, Section 8 (authentication); no raw NID number stored after verification |
| **Availability SLA** | 99.9% (NASC (National Identity Management Centre) SLA); portal implements circuit breaker with fallback |

### Nepal Document Wallet (NDW)

| Attribute | Value |
|-----------|-------|
| **Integration Type** | OAuth 2.0 + REST API (Nepal Document Wallet (NDW) Gateway v3) |
| **Purpose** | Pull citizen's verified government documents (driving licence, certificate, marksheet) |
| **Data Exchanged** | OAuth tokens, document metadata, document binary (PDF) |
| **Data Sensitivity** | Restricted PII; documents treated as sensitive |
| **Compliance** | Nepal Document Wallet (NDW) Act provisions under IT Act 2000; citizen must explicitly authorise each document pull |
| **Fallback** | If Nepal Document Wallet (NDW) unavailable, citizen can upload physical scans as fallback |

### ConnectIPS / Razorpay

| Attribute | Value |
|-----------|-------|
| **Integration Type** | REST API + HMAC-signed Webhooks |
| **Purpose** | Online fee collection (eSewa/Khalti/ConnectIPS, net banking, cards) for paid government services |
| **Data Exchanged** | Order ID, amount, currency, citizen ID, ARN; payment status (success/failure); transaction reference |
| **Data Sensitivity** | Financial; no card numbers stored in portal (PCI DSS compliance via ConnectIPS) |
| **Compliance** | RBI guidelines on payment aggregators; Government e-Payment Gateway mandate |
| **Idempotency** | Webhook processing is idempotent (duplicate webhooks rejected via DB lock) |

### SMS Gateway (Twilio / NIC SMS)

| Attribute | Value |
|-----------|-------|
| **Integration Type** | REST API |
| **Purpose** | OTP delivery, transactional notifications, SLA reminders, emergency broadcasts |
| **Data Exchanged** | Phone number (masked in logs), message content, delivery status |
| **Data Sensitivity** | Restricted (phone number is PII) |
| **Fallback** | NIC Nepal Telecom / Sparrow SMS gateway as secondary if primary Twilio fails |

### Email Service (AWS SES)

| Attribute | Value |
|-----------|-------|
| **Integration Type** | AWS SES SMTP / API |
| **Purpose** | Transactional emails: confirmations, receipts, certificates, reports |
| **Data Exchanged** | Email address, templated HTML/text content, attachments (PDFs) |
| **Data Sensitivity** | Restricted (email address is PII) |
| **Deliverability** | DKIM and SPF configured; bounce/complaint handling via SNS |

### National Citizen Registry

| Attribute | Value |
|-----------|-------|
| **Integration Type** | REST API (read-only) |
| **Purpose** | Validate address and demographic data on application submission |
| **Data Exchanged** | Citizen ID, address components, demographic validation flag |
| **Data Sensitivity** | Restricted PII |
| **Compliance** | Data sharing governed by inter-government data-sharing agreement |

### Department Legacy Systems

| Attribute | Value |
|-----------|-------|
| **Integration Type** | REST API (where available) or SFTP batch file exchange |
| **Purpose** | Fetch existing citizen records (land title, pension status); push approved application results |
| **Data Exchanged** | Structured records per department schema |
| **Data Sensitivity** | Varies by department; may include sensitive land and financial records |
| **Error Handling** | Failed syncs queued for retry; manual reconciliation dashboard for exceptions |

---

## Context Boundary Summary

```mermaid
flowchart TD
    subgraph Govt["Government IT Infrastructure"]
        NASC (National Identity Management Centre)["NASC (National Identity Management Centre) / NID\n(Identity)"]
        DL["Nepal Document Wallet (NDW)\n(Documents)"]
        PG["ConnectIPS\n(Payments)"]
        NCR["National Citizen Registry\n(Demographics)"]
        LS["Department Legacy Systems"]
    end

    subgraph Commercial["Commercial Services"]
        SMS["SMS Gateway\n(Twilio)"]
        EMAIL["Email / AWS SES"]
    end

    subgraph Portal["Government Services Portal\n(Within Scope)"]
        CP["Citizen Portal\n(Next.js)"]
        OC["Officer Console\n(Django)"]
        API["API Server\n(DRF)"]
        WF["Workflow Engine\n(Celery)"]
        DB["PostgreSQL + Redis\n(Data Layer)"]
        S3["Document Store\n(S3)"]
    end

    CITIZEN["👤 Citizen"] --> CP
    OFFICER["👮 Field Officer"] --> OC
    DHEAD["🏛 Dept Head"] --> OC
    SADMIN["⚙️ Super Admin"] --> OC
    AUDITOR["🔍 Auditor"] --> OC

    CP --> API --> WF --> DB
    OC --> API
    API --> S3

    API --> NASC (National Identity Management Centre)
    API --> DL
    API --> PG
    API --> NCR
    WF --> LS
    WF --> SMS
    WF --> EMAIL
```

---

## Compliance and Security Context

| Concern | Regulation | Portal Response |
|---------|-----------|----------------|
| NID Data Handling | NID Act 2016 | No raw NID stored; masked display; OTP verification only |
| PII Protection | PDPA 2023 (Nepal) | Encrypted at rest (AES-256), TLS 1.3 in transit |
| Financial Records | Companies Act 2013 | Fee records retained 7 years |
| Audit Logs | IT Act 2000, Sec 67C | Immutable, tamper-evident logs retained 7 years |
| RTI Disclosure | RTI Act 2005 | Proactive disclosure reports generated quarterly |
| e-Signatures | IT Act 2000, Sec 5 | DSC used for certificate signing |
| Payment Security | RBI Payment Aggregator Guidelines | No card data stored; PCI DSS via ConnectIPS |
