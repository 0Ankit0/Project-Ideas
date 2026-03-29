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

---

---

## Process Narrative (System context boundaries)
1. **Initiate**: Enterprise Architect captures the primary change request for **System Context Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to system context boundaries.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: API Gateway executes the approved path and enforces boundary policy checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm external dependency mapping.

## Role/Permission Matrix (System Context Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View system context diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (System context boundaries)
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> InReview: submit
    InReview --> Approved: functional + technical checks
    InReview --> Rework: feedback
    Rework --> InReview: resubmit
    Approved --> Released: publish/deploy
    Released --> Monitored: telemetry active
    Monitored --> Stable: controls pass
    Monitored --> Incident: control failure
    Incident --> Rework: corrective action
    Stable --> [*]
```

## Integration Behavior (System Context Diagram)
| Integration | Trigger | Expected Behavior | Failure Handling |
|---|---|---|---|
| IAM / RBAC | Approval or assignment change | Sync permission scopes for affected actors | Retry + alert on drift |
| Workflow/Event Bus | State transition | Publish canonical event with correlation ID | Dead-letter + replay tooling |
| Payroll/Benefits (where applicable) | Compensation/lifecycle change | Apply financial side-effects only after approved state | Hold payout + reconcile |
| Notification Channels | Review decision, exception, due date | Deliver actionable notice to owners and requestors | Escalation after SLA breach |
| Audit/GRC Archive | Any controlled transition | Store immutable evidence bundle | Block progression if evidence missing |

## Onboarding/Offboarding Edge Cases (Concrete)
- **Rehire with residual access**: If a rehire request reuses a prior identity, retain historical employee ID linkage but force fresh role entitlement approval before day-1 access.
- **Early start-date acceleration**: When onboarding date is moved earlier than background-check SLA, block activation and auto-create an exception approval task.
- **Same-day termination**: For involuntary offboarding, revoke privileged access immediately while preserving records under legal hold classification.
- **Rescinded resignation after downstream sync**: If offboarding is canceled after payroll/IAM notifications, execute compensating events and log full reversal trail.

## Compliance/Audit Controls
| Control | Description | Evidence |
|---|---|---|
| Segregation of duties | Requestor and approver cannot be the same identity for controlled actions | Approval chain + user IDs |
| Transition integrity | Only allowed state transitions can be persisted | Transition log + rejection reasons |
| Timely deprovisioning | Offboarding access revocation meets SLA targets | IAM revocation timestamp report |
| Financial reconciliation | Payroll-impacting changes reconcile before close | Payroll batch diff + sign-off |
| Immutable auditability | Controlled actions are archived in WORM/append-only storage | Hash, retention tag, archive pointer |

