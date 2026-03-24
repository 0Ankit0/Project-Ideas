# System Context Diagram

## Overview
The system context shows the Employee Management System and its interactions with external actors and systems.

---

## Main System Context Diagram

```mermaid
graph TB
    subgraph Actors
        Employee((Employee))
        Manager((Manager))
        HR((HR Staff))
        Payroll((Payroll Officer))
        Admin((Admin))
    end

    subgraph ExternalSystems
        BiometricDevice[Biometric / RFID Devices]
        EmailProvider[Email Service]
        SMSProvider[SMS Gateway]
        PushService[Push Notification Service]
        BankingSystem[Banking / Salary Disbursement System]
        ERP[ERP / Accounting System<br>SAP / QuickBooks / Tally]
        SSO[Identity Provider<br>SAML 2.0 / OAuth 2.0]
        Storage[Object Storage<br>Documents & Payslips]
    end

    subgraph "Employee Management System"
        EMS[FastAPI / REST Backend]
    end

    Employee -->|view payslips, apply leave, submit timesheets, self-assess| EMS
    Manager -->|approve leave, conduct appraisals, manage team| EMS
    HR -->|manage employee lifecycle, configure policies| EMS
    Payroll -->|process payroll, generate payslips, tax compliance| EMS
    Admin -->|configure system, manage roles, view audit logs| EMS

    BiometricDevice -->|attendance punch events| EMS
    EMS -->|transactional emails, payslip delivery| EmailProvider
    EMS -->|OTP, leave alerts| SMSProvider
    EMS -->|real-time alerts| PushService
    EMS -->|bank transfer file, salary disbursement| BankingSystem
    EMS <-->|employee data sync, payroll journal entries| ERP
    EMS <-->|SSO authentication| SSO
    EMS -->|store documents, payslips, reports| Storage
```

---

## Detailed Context With Data Flows

```mermaid
graph LR
    subgraph Clients
        ESS[Employee Self-Service Web]
        MSS[Manager Self-Service Web]
        HRUI[HR Portal]
        PayrollUI[Payroll Dashboard]
        AdminUI[Admin Console]
        MobileApp[Mobile App]
    end

    subgraph Platform
        API[REST API]
        WS[WebSocket Manager]
        Worker[Async Task Worker]
    end

    subgraph External
        Email[Email Provider]
        SMS[SMS Gateway]
        Push[Push Service]
        Bank[Banking System]
        ERP[ERP Integration]
        Biometric[Biometric Devices]
        IdP[Identity Provider]
        Storage[Object Storage]
    end

    ESS --> API
    MSS --> API
    HRUI --> API
    PayrollUI --> API
    AdminUI --> API
    MobileApp --> API

    API --> WS
    API --> Worker
    Worker --> Email
    Worker --> SMS
    Worker --> Push
    Worker --> Bank
    API <--> ERP
    Biometric --> API
    API <--> IdP
    API --> Storage
```

---

## Security Boundaries

```mermaid
graph TB
    subgraph "Public Zone"
        Internet[Internet]
        CDN[CDN]
    end

    subgraph "Edge Zone"
        WAF[Web Application Firewall]
        LB[Load Balancer]
    end

    subgraph "Application Zone"
        API[REST API Service]
        Worker[Async Worker]
        WS[WebSocket Manager]
        Cache[(Redis Cache)]
    end

    subgraph "Data Zone"
        DB[(Primary Database)]
        Storage[(Object Storage)]
    end

    subgraph "External Services"
        Email[Email / SMS / Push]
        Bank[Banking System]
        IdP[Identity Provider]
        Biometric[Biometric System]
    end

    Internet --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API
    API --> Cache
    API --> Worker
    API --> WS
    API --> DB
    API --> Storage
    API -- TLS --> Email
    API -- TLS --> Bank
    API -- TLS --> IdP
    Biometric -- TLS --> API
```

---

## External Dependency Notes

| System | Purpose | Integration Type |
|--------|---------|-----------------|
| Biometric / RFID Devices | Attendance punch recording | REST API push |
| Email Service | Payslip delivery, notifications, welcome emails | SMTP / API |
| SMS Gateway | OTP, leave and payroll alerts | API |
| Banking System | Salary disbursement file transfer | SFTP / API |
| ERP / Accounting | Payroll journal entries, employee master sync | REST / File |
| Identity Provider | SSO login for enterprise clients | SAML 2.0 / OAuth 2.0 |
| Object Storage | Document, payslip, and report storage | S3-compatible API |
| Push Notification | Mobile and web push for real-time alerts | FCM / APNs |
