# High-Level Architecture Diagram

## Overview
This document describes the high-level architecture of the Employee Management System. The system runs as a modular monolith with domain-separated modules, async task processing, WebSocket notifications, and integrations with biometric devices, banking, and ERP systems.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        ESS[Employee Self-Service\nWeb / Mobile]
        MSS[Manager Self-Service\nWeb]
        HRPortal[HR Portal\nWeb]
        PayrollUI[Payroll Dashboard\nWeb]
        AdminUI[Admin Console\nWeb]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[REST API Service]

        subgraph "Backend Modules"
            IAM[IAM & Auth]
            Employees[Employee Management]
            LeaveAttendance[Leave & Attendance]
            Payroll[Payroll]
            Performance[Performance & Goals]
            Benefits[Benefits & Compensation]
            Notifications[Notifications & WebSocket]
            Reports[Reports & Analytics]
            Admin[Admin & Configuration]
        end

        Worker[Async Task Worker]
    end

    subgraph "Data"
        DB[(PostgreSQL)]
        Redis[(Redis Cache)]
        Storage[(Object Storage)]
        Queue[(Task Queue)]
    end

    subgraph "External Services"
        BiometricSys[Biometric / RFID System]
        BankSystem[Banking / Disbursement]
        ERPSystem[ERP / Accounting]
        EmailSvc[Email Service]
        SMSSvc[SMS Gateway]
        PushSvc[Push Notification]
        IdP[Identity Provider\nSSO]
    end

    ESS --> CDN
    MSS --> CDN
    HRPortal --> CDN
    PayrollUI --> CDN
    AdminUI --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> Employees
    API --> LeaveAttendance
    API --> Payroll
    API --> Performance
    API --> Benefits
    API --> Notifications
    API --> Reports
    API --> Admin

    IAM --> DB
    Employees --> DB
    LeaveAttendance --> DB
    Payroll --> DB
    Performance --> DB
    Benefits --> DB
    Notifications --> DB
    Reports --> DB
    Admin --> DB

    IAM --> Redis
    LeaveAttendance --> Redis
    Payroll --> Redis

    Employees --> Storage
    Payroll --> Storage
    Reports --> Storage

    Payroll --> Queue
    Reports --> Queue
    Notifications --> Queue
    Queue --> Worker

    Worker --> EmailSvc
    Worker --> SMSSvc
    Worker --> PushSvc
    Worker --> BankSystem

    API --> IdP
    BiometricSys --> API
    API <--> ERPSystem
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[REST API Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis Cache)]

    Domain --> Event[Domain Event / Notification]
    Event --> Queue[(Task Queue)]
    Queue --> Worker[Async Worker]
    Worker --> WS[WebSocket Manager]
    Worker --> Msg[Email / SMS / Push]
    Worker --> Bank[Banking System]

    BiometricDevice[Biometric Device] --> API
    API --> External[ERP / SSO]
```

---

## Key Backend Module Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, SSO integration, 2FA, RBAC, session management |
| Employee Management | Employee profiles, org structure, onboarding, offboarding, documents |
| Leave & Attendance | Leave requests, approvals, balances, attendance recording, timesheets, shifts |
| Payroll | Payroll runs, salary computation, deductions, payslips, bank transfer, compliance |
| Performance & Goals | Appraisal cycles, goal setting, KRA ratings, PIP, 360-degree feedback |
| Benefits & Compensation | Benefit plans, enrolment, salary structures, revision workflows |
| Notifications | In-app, email, SMS, push; WebSocket fanout for real-time updates |
| Reports & Analytics | HR, payroll, leave, performance reports; executive dashboards |
| Admin & Configuration | Roles, permissions, system settings, audit logs, integrations |

---

## Current Architecture Notes

- The system is designed as a modular monolith that can be decomposed into microservices if scale demands
- Payroll processing and bulk report generation are handled asynchronously via task queue
- Biometric punch events are ingested via REST API with offline buffering support
- SSO integration supports SAML 2.0 and OAuth 2.0 for enterprise clients

---

---

## Process Narrative (Macro architecture blueprint)
1. **Initiate**: Enterprise Architect captures the primary change request for **Architecture Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to macro architecture blueprint.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Architecture Review Board executes the approved path and enforces architecture principle checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm system-wide cohesion.

## Role/Permission Matrix (Architecture Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View architecture diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Macro architecture blueprint)
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

## Integration Behavior (Architecture Diagram)
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

