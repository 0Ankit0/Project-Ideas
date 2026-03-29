# System Context Diagram

## Overview
The system context diagram shows the Student Information System boundaries, its primary actors, and all external systems it interacts with.

---

## Main System Context Diagram

```mermaid
graph TB
    subgraph Actors
        Student((Student))
        Faculty((Faculty))
        Advisor((Academic Advisor))
        Admin((Admin Staff))
        Registrar((Registrar))
        Parent((Parent/Guardian))
    end

    subgraph ExternalSystems
        PG[Payment Providers<br>Bank Transfer / Cards / UPI]
        SMS[SMS Provider]
        Email[Email Service]
        Push[Push Notification Service]
        LDAP[LDAP / SSO Provider]
        Storage[Object Storage]
        Library[Library Management System]
        ERP[Institution ERP / Finance System]
        BiometricDevice[Biometric Attendance Devices]
    end

    subgraph "Student Information System"
        Platform[SIS Platform<br>FastAPI Monolith]
    end

    Student -->|enroll, view grades, pay fees, download transcript| Platform
    Faculty -->|manage courses, record grades, mark attendance| Platform
    Advisor -->|view student progress, approve overrides| Platform
    Admin -->|manage users, courses, fees, reports| Platform
    Registrar -->|publish grades, issue transcripts, graduation| Platform
    Parent -->|view grades, attendance, fee status| Platform

    Platform -->|process fee payments| PG
    Platform -->|OTP and alerts| SMS
    Platform -->|transactional emails| Email
    Platform -->|push notifications| Push
    Platform <-->|authentication| LDAP
    Platform -->|store documents, transcripts, materials| Storage
    Platform <-->|book catalog and borrowing| Library
    Platform <-->|financial records sync| ERP
    Platform <-->|attendance data| BiometricDevice
```

---

## Detailed Context With Data Flows

```mermaid
graph LR
    subgraph Clients
        StudentWeb[Student Portal]
        StudentMobile[Student Mobile App]
        FacultyUI[Faculty Portal]
        AdminUI[Admin Dashboard]
        ParentUI[Parent Portal]
    end

    subgraph Platform
        API[REST API]
        WS[Websocket Manager]
    end

    subgraph Payments
        OnlineBanking[Online Banking]
        Cards[Credit/Debit Cards]
        UPI[UPI Gateway]
    end

    subgraph Messaging
        SMS[SMS Gateway]
        Email[Email Provider]
        Push[Push Provider]
    end

    subgraph Integrations
        LDAP[LDAP / SSO]
        Library[Library System]
        ERP[ERP / Finance]
        Storage[Object Storage]
        Biometric[Biometric Devices]
    end

    StudentWeb --> API
    StudentMobile --> API
    FacultyUI --> API
    AdminUI --> API
    ParentUI --> API

    API --> WS
    API --> OnlineBanking
    API --> Cards
    API --> UPI
    API --> SMS
    API --> Email
    API --> Push
    API <--> LDAP
    API <--> Library
    API <--> ERP
    API --> Storage
    API <--> Biometric
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
        API[SIS Application]
        Redis[Redis Cache]
        Worker[Async Task Worker]
        WS[Websocket Manager]
    end

    subgraph "Data Zone"
        DB[(Primary Database)]
        Storage[(Document Storage)]
    end

    subgraph "External Services"
        PG[Payment Providers]
        MSG[SMS / Email / Push]
        IAM[LDAP / SSO Provider]
        LIB[Library System]
    end

    Internet --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API
    API --> Redis
    API --> Worker
    API --> WS
    API --> DB
    API --> Storage
    API -- TLS --> PG
    API -- TLS --> MSG
    API -- TLS --> IAM
    API -- TLS --> LIB
```

---

## External Dependency Notes

| System | Purpose | Integration Type |
|--------|---------|-----------------|
| Payment providers | Fee collection and refunds | API integration |
| SMS / Email / Push | OTP, alerts, notifications | Third-party providers |
| LDAP / SSO | Institutional authentication | Directory service |
| Object storage | Documents, transcripts, materials | Cloud storage |
| Library system | Book catalog and borrowing | REST API sync |
| ERP / Finance | Fee reconciliation and financial records | Bidirectional sync |
| Biometric devices | Automated attendance capture | Device API / SDK |

## Implementation-Ready Addendum for System Context Diagram

### Purpose in This Artifact
Specifies inbound/outbound trust boundaries and data classifications.

### Scope Focus
- Boundary and trust-zone refinement
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

#### Implementation Rules
- Enrollment lifecycle operations must emit auditable events with correlation IDs and actor scope.
- Grade and transcript actions must preserve immutability through versioned records; no destructive updates.
- RBAC must be combined with context constraints (term, department, assigned section, advisee).
- External integrations must remain contract-first with explicit versioning and backward-compatibility strategy.

#### Acceptance Criteria
1. Business rules are testable and mapped to policy IDs in this artifact.
2. Failure paths (authorization, policy window, downstream sync) are explicitly documented.
3. Data ownership and source-of-truth boundaries are clearly identified.
4. Diagram and narrative remain consistent for the scenarios covered in this file.

